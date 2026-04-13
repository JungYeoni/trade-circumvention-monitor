# 변경 이력 (Changelog)

## 미출시 변경사항

### CI/CD

- CI에서 의미없는 ruff --fix 제거 ([c5fe2da](https://github.com/JungYeoni/da-template/commit/c5fe2daf4c3730ddb07576937648382781dc182d))
- Ruff format --check 추가로 포맷 불일치 CI 차단 ([3e8f382](https://github.com/JungYeoni/da-template/commit/3e8f382b698896126e58e3beb2e80c9bbdf29aa3))

### style

- Black 포맷 적용 ([803edf1](https://github.com/JungYeoni/da-template/commit/803edf13cdd66469c74c6be0b664889d28664316))

### 기타

- CHANGELOG 자동 업데이트 워크플로우 추가 (git-cliff) ([cb4777d](https://github.com/JungYeoni/da-template/commit/cb4777d787dc6481b03042084a695d5ac2eb976e))
- Docs/ gitignore 추가 ([e960045](https://github.com/JungYeoni/da-template/commit/e9600451af2c5e32d411b808fe3e72fad8fd3fee))
- Pre-commit 훅 추가 — ruff lint + format 자동 적용 ([8d33a13](https://github.com/JungYeoni/da-template/commit/8d33a13124257a6a8d290b3f5651b733fff96e02))
- Pyproject.toml에서 black 완전 제거, ruff format 설정 추가 ([2799e7b](https://github.com/JungYeoni/da-template/commit/2799e7b39b875e6fd1c30cfb03ef955e68833349))

### 문서

- [Docs] README에 Use this template 배지 추가 ([bd8c252](https://github.com/JungYeoni/da-template/commit/bd8c252de53f0507604338650ab59b48ad5533a8))

### 버그 수정

- Cliff.toml env.GITHUB_REPO 변수 오류 수정 ([a68e29c](https://github.com/JungYeoni/da-template/commit/a68e29c9a790684ee0524e106a8106ca99d63a8c))
- Git-cliff-action Docker Buster EOL 오류 수정 ([5bb2c8b](https://github.com/JungYeoni/da-template/commit/5bb2c8bb2a06560c1cd59ce137e5b10f37b63dc9))
- Ruff I001 import 정렬 수정 ([df86e5e](https://github.com/JungYeoni/da-template/commit/df86e5ed990c20127f7ce64858e4fdc151d7ed63))
- CI에서 black 제거 — ruff로 스타일 체크 통합 ([ce5fb50](https://github.com/JungYeoni/da-template/commit/ce5fb503ad9a90c997020b12c32c51fd10a7d0dd))
- Ruff --fix로 import 정렬 자동 적용 후 체크 ([19ec536](https://github.com/JungYeoni/da-template/commit/19ec536cb161143a3cf75dd0e6ef218442456ba9))
- Ruff lint 오류 수정 ([5eedae6](https://github.com/JungYeoni/da-template/commit/5eedae647534e4c2aca44b9cd40ad52b327d33f1))
- CI 실패 수정 — build-backend 오타, GIS 의존성 분리 ([76771b1](https://github.com/JungYeoni/da-template/commit/76771b1ad21d2cbf325d849538bf4a977b7bcfd2))

### 새 기능

- 데이터분석·ML 프로젝트 템플릿 전체 구성 ([07fbb5b](https://github.com/JungYeoni/da-template/commit/07fbb5bafcd6d59039816e44756597bfe0511820))
- 분석 슬래시 커맨드 6종 추가 및 README 작성 ([cf20bf9](https://github.com/JungYeoni/da-template/commit/cf20bf9e414eedb7f61008b3ead25b347a427b2c))
- 데이터 분석 Claude 전역 설정 초기 구성 ([b99887c](https://github.com/JungYeoni/da-template/commit/b99887ced270db03295a8dadd224732a6947a2eb))


