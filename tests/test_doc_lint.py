"""v3.2.2 (REQ-V3.2.2-010): doc-lint——SKILL.md 内嵌命令与实现契约的一致性测试。
根因: R0 文档命令按 2 元组解包而 smoke_test 返回 3 元组 (mbedtls 审计 ValueError)——
文档内嵌代码漂移必须由测试捕获, 而非审计现场发现。"""
import json
import os
import re
import subprocess
import sys
import tempfile

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL_MD = os.path.join(WORKSPACE, "SKILL.md")


def _code_blocks():
    text = open(SKILL_MD).read()
    return re.findall(r"```(?:bash)?\n(.*?)```", text, re.S)


def test_r0_selfcheck_is_single_source():
    """R0 签名库自检必须是 selfcheck 一条命令; 禁止内嵌 smoke_test 多行命令。"""
    blocks = _code_blocks()
    r0_blocks = [b for b in blocks if "signature_lib" in b]
    assert r0_blocks, "SKILL.md 无签名库自检命令块"
    for b in r0_blocks:
        # 内嵌 python3 -c 的多行自检是文档漂移形态 (mbedtls 实测 ValueError 源头)
        assert "python3 -c" not in b, f"内嵌自检命令未收敛到 selfcheck:\n{b}"
    assert any("selfcheck" in b for b in r0_blocks), "R0 缺 selfcheck 命令"


def test_selfcheck_command_runs_on_nonfixture_project():
    """照抄 SKILL.md 的 R0 命令, 对非 fixture 项目真实执行 → exit 0 (完整性自检)。"""
    blocks = _code_blocks()
    cmdline = None
    for b in blocks:
        for line in b.splitlines():
            # 只认命令形态行 (python3 开头)——fence 跨段误配对时散文行
            # ("- R0 `signature_lib.py selfcheck` 不受影响...") 不得被当命令执行
            if "selfcheck" in line and "signature_lib" in line \
               and line.strip().startswith("python3"):
                cmdline = line.strip()
    assert cmdline, "SKILL.md 无 selfcheck 命令行"
    with tempfile.TemporaryDirectory() as tmp:
        # 模拟 skill 目录布局: 把 workspace 的 signature_lib 当作 <skill_dir> 的模块
        cmd = cmdline.replace("<skill_dir>", WORKSPACE).replace("<project>", tmp)
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                           cwd=WORKSPACE)
        assert r.returncode == 0, f"selfcheck 失败:\n{r.stdout}\n{r.stderr}"


def test_skill_runtime_imports_are_contract_stable():
    """R0/harness 自检依赖的入口签名与实现一致 (3 元组契约)。"""
    sys.path.insert(0, WORKSPACE)
    import signature_lib
    d = signature_lib.load()
    results, rate, testable = signature_lib.smoke_test(d, ["/nonexistent-repo"])
    assert isinstance(results, dict) and isinstance(rate, float) \
        and isinstance(testable, int)
    assert "__integrity__" in results


def test_lessons_recorder_lenient_resurrection_review():
    """REQ-V3.2.2-015: str 形态 resurrection_review 不再崩溃 (mbedtls 实测)。"""
    import tempfile
    import importlib
    sys.path.insert(0, WORKSPACE)
    lr = importlib.import_module("lessons_recorder")
    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, ".audit_results"))
        json.dump({"schema_version": "3.0", "candidates": [
            {"id": "CAND-X", "status": "VERIFIED", "verdict": "UNREACHABLE",
             "resurrection_review": "复活攻击 N=1: revived=false (str 形态)"}],
            "r4_findings": [], "target_kind": "library"},
            open(os.path.join(tmp, ".audit_results", "verify_queue.json"), "w"))
        fn = getattr(lr, "collect", None)
        assert callable(fn), "lessons_recorder 无 collect 入口"
        out = fn(tmp)  # str 形态不再 AttributeError 即为通过
        assert isinstance(out, dict) and "issues" in out


def test_checklist_pinned_dep_entry():
    """v3.4.5 (SWR-V3.4.5-004): CK-PINNED-DEP 条目结构完整 + 去项目化
    (第一原则: 资产不得携带项目专属名, 来源只留追溯字段)。"""
    import json as _json
    p = os.path.join(WORKSPACE, "resources", "checklist_library.json")
    d = _json.load(open(p))
    entry = next(c for c in d["checklists"] if c["id"] == "CK-PINNED-DEP")
    assert entry["family"] == "vendored-deps"
    assert entry["applies_to"] == ["verifier", "refuter"]
    assert len(entry["steps"]) == 4
    blob = _json.dumps(entry, ensure_ascii=False).lower()
    for name in ("grpc", "boringssl", "jsrsasign", "sinatra", "lighttpd", "mbedtls"):
        assert name not in blob, f"CK-PINNED-DEP 含项目专属名 {name}"
