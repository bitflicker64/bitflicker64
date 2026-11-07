<!-- AUTO-GENERATED from README.template.md — do not edit by hand -->
<div align="center">

# Himanshu Verma

**Maintainer of [Kepler](https://github.com/sustainable-computing-io/kepler), a CNCF Sandbox project** · Technical Committee member · [listed in MAINTAINERS.md](https://github.com/sustainable-computing-io/kepler/blob/main/MAINTAINERS.md)

Backend & infrastructure

Guest on [Apache PlusOne](https://plusone.apache.org/2026/11/02/apache-hugegraph-with-himanshu-verma/), the official ASF podcast, talking about Apache HugeGraph (Nov 2026)

[Portfolio](https://killl.me) · [LinkedIn](https://linkedin.com/in/himanshu-verma-40755a359) · [X](https://x.com/Bitflicker64)

</div>

Maintainer and Technical Committee member on [Kepler](https://github.com/sustainable-computing-io/kepler), a CNCF Sandbox project that measures the energy use of Kubernetes workloads. I work on its GPU device layer, Helm manifests and e2e/CI, and review across the project.

I work on reliable infrastructure: Docker/ops tooling, networking observability, and production graph systems. **100 merged upstream PRs** across the Apache HugeGraph ecosystem, Cilium, PipeCD, and others — healthchecks, process supervision, networking, auth, CI, and docs that keep systems operable.

Currently contributing around Kubernetes, containerd, Cilium, and chaos/observability tooling.

## Talks and media

- **Apache PlusOne, the official podcast of the Apache Software Foundation (November 2026):** [Apache HugeGraph, with Himanshu Verma](https://www.youtube.com/watch?v=yuq_AQ0C4cI) ([audio and episode page](https://plusone.apache.org/2026/11/02/apache-hugegraph-with-himanshu-verma/)). Why graphs matter for AI retrieval, how HugeGraph compares to Neo4j, JanusGraph and Apache AGE, the 1.8 release work, and how to start contributing.

## Upstream work

| Project | PRs | Focus |
| --- | --- | --- |
| [Apache HugeGraph ecosystem](https://github.com/pulls?q=is%3Apr+author%3Abitflicker64+org%3Aapache+hugegraph) | 70 merged · 26 open | Docker healthchecks, process supervision, bridge networking, CI, auth, and ops docs.<br><sub>Latest: <a href="https://github.com/apache/hugegraph-doc/pull/538">#538</a> — docs(pd): document the raft connect and install-snapshot timeouts</sub> |
| [Cilium / Hubble](https://github.com/cilium/cilium/pulls?q=is%3Apr+author%3Abitflicker64) | 7 merged | Hubble metrics label parsing, docs fixes, contributor tooling cleanup.<br><sub>Latest: <a href="https://github.com/cilium/cilium/pull/48870">#48870</a> — helm: allow removing port 80 from the cilium-ingress service</sub> |
| [containerd](https://github.com/containerd/containerd/pulls?q=is%3Apr+author%3Abitflicker64) | 0 merged · 1 open | Content-store size filtering (`AdaptInfo`) and CRI-adjacent work.<br><sub>Open: <a href="https://github.com/containerd/containerd/pull/13576">#13576</a> — content: support size based filtering in AdaptInfo</sub> |
| [Kubernetes ecosystem](https://github.com/pulls?q=is%3Apr+author%3Abitflicker64+(repo%3Akubernetes%2Fkubernetes+OR+repo%3Achaos-mesh%2Fchaos-mesh+OR+repo%3Asustainable-computing-io%2Fkepler+OR+repo%3Apipe-cd%2Fpipecd)) | 4 merged · 6 open | Cluster tooling, chaos e2e hygiene, energy exporter manifests, CD docs.<br><sub>Latest: <a href="https://github.com/sustainable-computing-io/kepler/pull/2599">#2599</a> — test(e2e): run the GPU e2e tests on a real NVIDIA GPU</sub> |

## Open PRs

Live snapshot of open pull requests in upstream orgs (auto-refreshed).

- [apache/hugegraph#3465](https://github.com/apache/hugegraph/pull/3465) — fix(pd): trim the partition graph name once and keep two causes
- [apache/hugegraph#3464](https://github.com/apache/hugegraph/pull/3464) — fix(store): correct small iterator, compare and hash edge cases
- [apache/hugegraph#3463](https://github.com/apache/hugegraph/pull/3463) — fix(cluster-test): return PD REST addresses and retry node cleanup
- [apache/hugegraph#3462](https://github.com/apache/hugegraph/pull/3462) — fix(dist): keep the cause when a plugin or Gremlin Server fails
- [apache/hugegraph#3461](https://github.com/apache/hugegraph/pull/3461) — fix(rocksdb): skip empty SST tables on close and close listCFs options
- [apache/hugegraph#3460](https://github.com/apache/hugegraph/pull/3460) — fix(api): report a missing Cypher config file and close its reader
- [apache/hugegraph#3459](https://github.com/apache/hugegraph/pull/3459) — refactor(core): use pattern matching and close readers on all paths
- [apache/hugegraph#3458](https://github.com/apache/hugegraph/pull/3458) — fix(core): close merged origin iterator and fix two edge cases
- [apache/hugegraph#3457](https://github.com/apache/hugegraph/pull/3457) — fix(commons): correct small perf and util edge cases
- [apache/hugegraph#3456](https://github.com/apache/hugegraph/pull/3456) — fix(commons): close batch iterators and keep failure causes
- [apache/hugegraph#3455](https://github.com/apache/hugegraph/pull/3455) — refactor(struct): use pattern matching and close LZ4 streams
- [apache/hugegraph#3454](https://github.com/apache/hugegraph/pull/3454) — fix(struct): correct small schema, analyzer and edge label bugs

## Stats

<p align="center">
  <img height="170em" src="https://github-readme-stats-one-bice.vercel.app/api?username=bitflicker64&show_icons=true&theme=transparent&hide_border=true&title_color=38C2FF&text_color=BDC3CF&icon_color=38C2FF&count_private=true&include_all_commits=true" alt="GitHub stats"/>
  <img height="170em" src="https://github-readme-stats-one-bice.vercel.app/api/top-langs/?username=bitflicker64&layout=compact&theme=transparent&hide_border=true&title_color=38C2FF&text_color=BDC3CF&card_width=445" alt="top languages"/>
</p>

## Tools

Java · Go · Python · JavaScript · SQL · Spring Boot · Kubernetes · Docker · containerd · Cilium · GitHub Actions · Linux

---

<sub>Auto-updated 2026-11-07 17:46 UTC · [workflow](.github/workflows/update-readme.yml)</sub>
