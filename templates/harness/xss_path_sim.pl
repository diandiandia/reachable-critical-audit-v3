#!/usr/bin/perl
# R5-2: 反射 XSS 路径模拟器 — 参数化通用骨架 (v3.5 去项目化重写)
#
# 用法: perl xss_path_sim.pl '<json 链描述>'
#   json 链描述: {"decode_chain":["<解码函数:decode_cgi_percent|decode_utf8|none>"],
#    "sanitize_chain":["<净化函数:strip_angle_pipes|strip_onload|xmlencode_identity|none>"],
#    "sink":"<属性嵌入模板, %s 为载荷位>", "payload":"<攻击载荷>", "match":"<存活判定正则>"}
#
# 语义: 按「解码 → 净化 → 属性嵌入 → 载荷存活判定」执行, 模拟
#   CGI 参数捕获链中 净化函数缺失引号剥离 的经典缺口形态 (属性注入)。
# 各步骤为通用形态, 不绑定任何具体项目; 历史战役精确复刻存放于
#   tests/fixtures/ 同名锚点文件 (第一原则三禁止③豁免), 本骨架须能复现其裁决语义。
use strict; use warnings;

sub decode_cgi_percent { my $s = shift; $s =~ s/%([0-9A-Fa-f]{2})/chr(hex($1))/eg; return $s; }
sub decode_utf8        { my $s = shift; $s =~ s/\\u([0-9A-Fa-f]{4})/chr(hex($1))/eg; return $s; }
sub strip_angle_pipes  { my $s = shift; $s =~ s/[<>|]//g; return $s; }
sub strip_onload       { my $s = shift; $s =~ s/onload//gi; return $s; }
sub xmlencode_identity { return shift; }

my $arg = shift @ARGV;
die "usage: xss_path_sim.pl '<json chain description>'\n" unless defined $arg;

my %d;
if (eval { %d = %{decode_json($arg)}; 1 }) {
    # JSON::PP 属 perl 核心 (5.14+)
    my $s = $d{payload} // '%22%20onmouseover%3D%22alert(document.domain)%2F%2F';
    for my $fn (@{ $d{decode_chain} || [] }) {
        no strict 'refs';
        $s = &{"decode_$fn"}($s) if defined &{"decode_$fn"};
    }
    for my $fn (@{ $d{sanitize_chain} || [] }) {
        no strict 'refs';
        $s = &{"sanitize_$fn"}($s) if defined &{"sanitize_$fn"};
    }
    my $sink  = $d{sink}  // '<img src="%s/logo.png" border="0">';
    my $match = $d{match} // 'onmouseover=';
    my $out = sprintf $sink, $s;
    print "after sanitize: [$s]\n";
    print "rendered: $out\n";
    if ($out =~ /$match/) {
        print "VERDICT: XSS payload SURVIVES into attribute — REACHABLE\n";
        exit 0;
    }
    print "VERDICT: payload blocked\n";
    exit 1;
} else {
    die "invalid JSON: $arg\n";
}

# JSON::PP 无 use 时兜底 (保持单文件可跑)
sub decode_json { require JSON::PP; return JSON::PP::decode_json($_[0]); }
