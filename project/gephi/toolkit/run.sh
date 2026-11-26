#!/usr/bin/env bash
# Compile and run the headless Gephi Toolkit pipeline.
# Usage: gephi/toolkit/run.sh MODE [ARGS...]
#   MODE = type | authors | r4 | conv | verify [file.gephi] | all
#          recolor_authors | layout_conv_full            (fix-round modes: open the saved project, no new modularity run)
#          relayout_authors SCALING GRAVITY STRONG ITERS OVERLAP THREADS [LINLOG]
#          relayout_conv    SCALING GRAVITY STRONG ITERS OVERLAP THREADS
#   Final settings used for the submitted figures:
#          relayout_authors 10 1 true 1500 200 4      relayout_conv 1 8 false 2000 200 4
#   'authors' and 'conv' now use these same settings by default.
#   WARNING: authors, r4, conv and all re-run Gephi Modularity / ForceAtlas2, which are not bit-for-bit repeatable
#   (class numbers and positions can shift), and they overwrite figures/, projects/ and stats/.
#   After any mode that writes a PDF: python pdf_to_png.py 4000 ../figures/<name>.pdf (needs pymupdf), then python make_slides.py.
# Requires a JDK 17+ (tested with JDK 23). Override with JAVA_HOME.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ARCH="$(cd "$HERE/../.." && pwd)"
JAVA_HOME="${JAVA_HOME:-/Library/Java/JavaVirtualMachines/jdk-23.jdk/Contents/Home}"
JAR="$HERE/lib/gephi-toolkit-0.11.4-all.jar"
BUILD="${GEPHI_BUILD_DIR:-${TMPDIR:-/tmp}/gephi_toolkit_build}"
EXPECTED_SHA="2a2f8226230965120d9c6037c93a97b685d976366bc959aab33912cf47365afa"
if [ ! -f "$JAR" ]; then
  mkdir -p "$HERE/lib"
  curl -fsSL -o "$JAR" https://repo1.maven.org/maven2/org/gephi/gephi-toolkit/0.11.4/gephi-toolkit-0.11.4-all.jar
fi
echo "$EXPECTED_SHA  $JAR" | shasum -a 256 -c -
mkdir -p "$BUILD"
"$JAVA_HOME/bin/javac" -nowarn -d "$BUILD" -cp "$JAR" "$HERE/src/GephiRun.java"
run() {
  local m="$1"; shift
  "$JAVA_HOME/bin/java" -Djava.awt.headless=true -Xmx6g -cp "$BUILD:$JAR" GephiRun "$m" "$ARCH" ${@+"$@"}
}
MODE="${1:-all}"
if [ "$MODE" = "all" ]; then
  for m in type authors r4 conv verify; do run "$m"; done
else
  shift || true
  run "$MODE" ${@+"$@"}
fi
