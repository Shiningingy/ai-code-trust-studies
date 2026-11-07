#!/bin/bash
# Zitadel's git-ignored generated Go code, following apps/api/project.json (generate-stubs,
# generate-statik without the pnpm/sass CSS step, generate-assets). Tools are in /opt/zbin
# (installed at setup); buf's dependency cache is in the image, so this runs offline.
set -e
cd "${1:-/work}"
export PATH=/opt/zbin:$PATH
buf generate
mkdir -p pkg/grpc openapi/v2/zitadel
cp -r .artifacts/grpc/github.com/zitadel/zitadel/pkg/grpc/* pkg/grpc/
cp -r .artifacts/grpc/zitadel/ openapi/v2/zitadel
for g in internal/api/ui/login/statik/generate.go internal/notification/statik/generate.go internal/statik/generate.go; do
  [ -f "$g" ] && go generate "$g"
done
if [ -f internal/api/assets/generator/asset_generator.go ]; then
  mkdir -p docs/apis/assets
  go run internal/api/assets/generator/asset_generator.go -directory=internal/api/assets/generator/ -assets=docs/apis/assets/assets.md
fi
