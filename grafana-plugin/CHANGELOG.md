# Changelog

## [1.9.28](https://github.com/grafana/irm/compare/grafana-oncall-app-v1.9.27...grafana-oncall-app-v1.9.28) (2024-10-01)


### Bug Fixes

* disallow oncall schedule rotation layer/overrides CUD form submissions more than once ([#193](https://github.com/grafana/irm/issues/193)) ([73ae1c7](https://github.com/grafana/irm/commit/73ae1c7d78474b42b9eb4305416828afeb04fa3a))


### Miscellaneous Chores

* implement merged IRM module.tsx ([#182](https://github.com/grafana/irm/issues/182)) ([995b573](https://github.com/grafana/irm/commit/995b5732493aabc226cd62b9ca52a1e582ef5878))

## [1.9.27](https://github.com/grafana/irm/compare/grafana-oncall-app-v1.9.26...grafana-oncall-app-v1.9.27) (2024-09-26)


### Bug Fixes

* address RBAC Admin issue ([#183](https://github.com/grafana/irm/issues/183)) ([508857b](https://github.com/grafana/irm/commit/508857b719641ce405910bb1b110dec62f1a7af5))
* Bring webhooks to IRM ([#144](https://github.com/grafana/irm/issues/144)) ([1a883e1](https://github.com/grafana/irm/commit/1a883e1e44fe154ec0a7d36fa8183444fb90c773))
* run go mod tidy ([#174](https://github.com/grafana/irm/issues/174)) ([df2cf75](https://github.com/grafana/irm/commit/df2cf75ac5d4f57661af722f4785ef4996644bbc))
* style links in incident message ([#143](https://github.com/grafana/irm/issues/143)) ([2e55b07](https://github.com/grafana/irm/commit/2e55b07c1069cebfb30ba944b1c0b6f7dbfb1bad))


### Dependencies

* bump `github.com/grafana/grafana-plugin-sdk-go` to `v0.250.2` to address CVE-2024-8986 ([#173](https://github.com/grafana/irm/issues/173)) ([2385dc3](https://github.com/grafana/irm/commit/2385dc39e0108ca8ee4047046a34a735d1598ec8))
* bump micromatch version from 4.0.6 to 4.0.8 ([#181](https://github.com/grafana/irm/issues/181)) ([b1123fd](https://github.com/grafana/irm/commit/b1123fd8d54db080eb90c9959494a3bd00a89540))


### Miscellaneous Chores

* release main ([#157](https://github.com/grafana/irm/issues/157)) ([1b2901c](https://github.com/grafana/irm/commit/1b2901c952cc8e82f94becfa44db146fc0abe076))
* release main ([#187](https://github.com/grafana/irm/issues/187)) ([3221340](https://github.com/grafana/irm/commit/3221340148ac972ed32cd16194a5eaf3cc29db3d))
* release main ([#190](https://github.com/grafana/irm/issues/190)) ([e2489d0](https://github.com/grafana/irm/commit/e2489d0a31c4ac80dc72dca57c42eb3068fa4661))

## [1.9.26](https://github.com/grafana/irm/compare/grafana-oncall-app-v1.9.25...grafana-oncall-app-v1.9.26) (2024-09-23)


### Bug Fixes

* fix template editor layout ([#142](https://github.com/grafana/irm/issues/142)) ([c8ac3b0](https://github.com/grafana/irm/commit/c8ac3b0f60cb5472fb93b59255ca30bc8ba64653))
* make sure GMT elem is selected from the dropdown options is sele… ([#141](https://github.com/grafana/irm/issues/141)) ([cc86f17](https://github.com/grafana/irm/commit/cc86f1751f7378d981d6e60a20cef746f090f1df))
* rename OnCall notification titles ([#126](https://github.com/grafana/irm/issues/126)) ([7df0120](https://github.com/grafana/irm/commit/7df01208271b29640939730375d035b5d5a13f98))
* update how config page is rendered in cloud ([#137](https://github.com/grafana/irm/issues/137)) ([3cf9bc2](https://github.com/grafana/irm/commit/3cf9bc23bee92dd8dde77fe225efebaeaf38a233))


### Miscellaneous Chores

* improve (again) ui pod readiness probe ([#120](https://github.com/grafana/irm/issues/120)) ([c4ee02b](https://github.com/grafana/irm/commit/c4ee02b5253a7cfaf983518c6475f6207a66e253))
