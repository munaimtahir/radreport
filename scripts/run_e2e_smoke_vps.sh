#!/bin/bash
export E2E_BASE_URL=http://127.0.0.1:8081
export E2E_API_BASE=http://127.0.0.1:8015/api
export E2E_USER=admin
export E2E_PASS=admin123
npm run e2e:smoke | tee ARTIFACTS/e2e_run.txt
