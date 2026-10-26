#!/usr/bin/env python3
"""Use the build's ktfmt cache to format/check only the changed Kotlin file."""
from pathlib import Path
import subprocess
import sys

cache = Path('/opt/vector-s26-tools/gradle-home/caches/modules-2/files-2.1')
groups = ['com.facebook', 'com.google.googlejavaformat', 'com.google.guava',
          'org.jetbrains.kotlin', 'org.jetbrains.intellij.deps',
          'org.jetbrains', 'com.google.errorprone', 'com.google.j2objc',
          'org.checkerframework', 'com.github.javaparser', 'org.jetbrains.kotlinx',
          'net.java.dev.jna', 'org.ec4j.core']
jars = sorted({str(p) for group in groups for p in (cache / group).rglob('*.jar')})
command = ['java', '-cp', ':'.join(jars), 'com.facebook.ktfmt.cli.Main']
sys.exit(subprocess.run(command + sys.argv[1:]).returncode)
