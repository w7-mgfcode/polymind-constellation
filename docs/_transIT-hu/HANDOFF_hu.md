# Session Átadás (Handoff)

> **Dátum:** 2026-07-23
> **Munkamenet fókusz:** A 0.8.1 megerősítés (hardening) áttekintésének befejezése, a következő
architektonikai irányok rangsorolása, valamint a kiadásautomatizálás és az aláírt
eredet-igazolás (signed provenance) implementálása.
> **Állapot:** A helyi implementálás és validáció kész. A távoli közzététel a Git, GitHub,
PyPI és aláíró konfiguráció hiánya miatt blokkolva van.

---
## Összefoglaló

A Polymind Constellation 0.8.1 kiadás helyben kész a közzétételre, de nem került még publikálásra.
A végponti (end-to-end) áttekintés első körében a *fail-closed* vetítés, szimbolikus link,
telepítő forráskiválasztás, valamint a megfelelőségi állapot (conformance-state) réseit zártuk.
Egy később architektonikai áttekintés során a kiadásautomatizálást 94/100, az eredet-igazolást 89/100,
míg a registry közzétételt 47/100 ponttal rangsorolta. A kiadásautomatizálás és az eredet-igazolás
került kiválasztásra az implementáláshoz; a registry közzététel a 9. fázisra halasztódott.

A tárház mostantól tartalmaz:
- egy tag-based GitHub Actions release pipeline-t,
- PyPI Trusted Publishing-et,
- determinisztikus kiadási bizonyítékot (evidence),
- közvetlen Gitsign commit ellenőrzést,
- GitHub/Sigstore SLSA artefaktum tanúsításokat (attestations).

A standard ellenőrzés sikeres. A release-módusban történő orchestráció sikeres egy eldobható,
valódí Git tárházban kontrollált verifikátor csatolók (stubs) használatával, míg a valódí
kriptográfiai ellenőrzés szándékosan blokkolva van amíg a valódí GitHub tárház ki nem állítja
a tanúsításokat.

A prioritás szerinti maradék backlog a [prioritized-todo.md](../prioritized-todo.md) fájlban található.

---
## Elvégzett munka

### 0.8.1 megerősítés (hardening)

- Visszaállítottuk az előzőleg generált vetítést (projection) minden kezelés alatti atomi
  cserehatár (atomic-replacement boundary) megszakítás után.
- Elutasítottuk a szimbolikus linkkel (symlink) ellátott kanonikus gyököket, csomagkönyvtárakat,
  erőforrásokat, telepítő gyököket és generált vetítési elérési útvonalaikat.
- eltávolítottuk a munkakönyvtár (working-directory) vetítés árnyékolását.
- A telepített kiadások a kerék (wheel) csomagba ágyazott vetítést részesítik előnyben.
- A forrás-ellenőrzési (source-checkout) vetítés keresést a framework modulhoz rögzítettük.
- Megőriztük a *pass*, *partial*, *skip*, *measured* és *fail* megfelelőségi állapotokat.
- Høzzáadtuk a vetítés hibainjekciós (fault-injection), symlink, telepítő-forrás és
  megfelelőségi regressziós teszteket.
- Frissítettük a framework-öt, a lock fájlt, a változásnaplót (changelog), a biztonsági,
  kompatibilitási és a 8. fázis kiadási dokumentációját a 0.8.1-es verzióra.

### Kiadásautomatizálás

- Høzzáadtuk a `.github/workflows/ci.yml` fájlt pull-request és push validálásához.
- Høzzáadtuk a `.github/workflows/release.yml` fájlt verzió-tag alapú kiadásokhoz.
- Høzzáadtuk a havi GitHub Actions függőség-monitorozást.
- Minden harmadik féltől származó action-t egy 40 karakteres commit SHA-hoz rögzítettünk.
- A kerék (wheel) és forrás archívumok dedikált build munkafolyamatban készülnek.
- Determinisztikus SHA-256 bizonyítékot és változásnapló alapú kiadási jegyzeteket generálunk.
- Védett pypi környezetben és PyPI Trusted Publishinggel dolgozunk.
- A hosszú életű PyPI token-eket és Twine jelszavakat kizártuk a workflow-ból.
- A GitHub Release-t csak a sikeres PyPI közzététel után hoztuk létre.
- Teszteket írtunk a workflow engedélyek, action rögzítések, közzétételi sorrend,
  valamint a token-alapú közzététel hiánya ellenőrzéséhez.

### Git és artefaktum eredet-igazolás (provenance)

- Høzzáadtuk a `polymind release-manifest`-et.
- Høzzáadtuk a `scripts/verify --release` paranccsal.
- Kötelező, hogy a HEAD, a pontos verzió tag és a manifest commit megegyezzen.
- Kötelező egy tiszta nyomon követett index és worktree.
- Kötelező pontosan egy várható kerék (wheel) és forrás archívum.
- Ellenőrizzük az artefaktum nevének, méretének és SHA-256 hash-ének egyezését.
- Kötelező a közvetlen Gitsign ellenőrzés a release commit-ra.
- Kötelező egy pontos tanúsítványazonosság (certificate identity) és pontos OIDC kiállító (issuer).
- Kötelező egy kulcs nélküli (keyless) GitHub/Sigstore tanúsítás mindkét artefaktumra.
- A tanúsítás ellenőrzését rögzítettük:
  - az elvárt tárházra;
  - `.github/workflows/release.yml`-re;
  - a pontos forrás commit-ra;
  - `refs/tags/v0.8.1`-re;
  - az SLSA provenance v1 predikátumra.
- A Gitsign 0.16.1 letöltése csak a SHA-256
  `4a29a1f4b9add1f0f6d9a3e9e6ba0cffa121b971be82d62bb1496d7d1d877b0a`
  ellenőrzése után történt.
- Negatív teszteket adtunk hozzá a hiányzó Git eredet-igazolás, artefaktum drift,
  hiányzó manifestek, érvénytelen Gitsign validáció, valamint hiányzó vagy érvénytelen
  tanúsítások ellenőrzéséhez.

### Architektonikai tervezés

- Rögzítettük a súlyozott rangsorolást a
  [development-directions.md](../development-directions.md) fájlban.
- Dokumentáltuk az egyalkalmas beállítást és a kiadási műveleteket a
  [release-automation.md](../release-automation.md) fájlban.
- Az OCI Distribution 1.1 plus ORAS-t választottuk a 9. fázis registry
  architektúraként.
- A registry kiadó és katalógus integráció halasztódott amíg a kiadási azonosítás
  és eredet-igazolás működőképes nem lesz.
- Létrehoztunk egy prioritás-, komplexitás-, és függőség-alapú backlogot a
  [prioritized-todo.md](../prioritized-todo.md) fájlban.

---
## Architektonikai döntések

- **A kiadásautomatizálás és eredet-igazolás megelőzi a registry közzétételt.**
  Egy registry nem oszthat ki csomagokat amíg a változhatatlan kiadási azonosítás és
  artefaktum validáció működőképes nem lesz.

- **PyPI Trusted Publishing használata hosszú életű feltöltési token helyett.**
  A közzétételi munkafolyamat csak a munkafolyamat-szintű OIDC engedélyt kap, ami
  rövid életű hitelesítést hoz létre.

- **Mind a forrás, mind a build azonosítás kötelező.**
  A Gitsign bizonyítja a jóváhagyott kiadási commit aláíróját. A GitHub/Sigstore
  tanúsítás külön bizonyítja a hostolt workflow-öt és a forrás-ből-artefaktumba
  kapcsolódást.

- **Pontos aláírói azonosítás rögzítése.**
  A kiadási validáció nem fogad el nem megnevezett aláírót, vagy azonosító regex-et.

- **SLSA Build Level 2 őszinte cél.**
  A Level 3 nem lett igénybe véve, mivel a build és aláíró logika még nem került át
  egy megerősített, újrahasznosítható workflow-ba.

- **A manifest metaadatokként kezelendő, nem aláírásként.**
  Egy checksum manifest érvénytelen Gitsign és Sigstore validáció nélkül elégtelen.

- **OCI és ORAS használata a 9. fázisban.**
  A tartalom-alapú generikus artefaktumok, referensek, és meglévő registry autorizáció
  preferált egyéni S3 és DynamoDB protokollal szemben.

- **Kanonikus skill-ek a `skills/` könyvtárban.**
  A generált provider vetületek (projections) csak olvashatóak maradnak, és újra
  generálhatók a meglévő szinkronizációs parancs használatával.

---
## Eredet-igazolási szerződés (Provenance Contract)

Egy kiadás **kötelezően meghiúsul**, ha a következő kijelentések bármelyike hamis:

1. A kiadási ref pontosan `refs/tags/v0.8.1`.
2. A HEAD, a tag commit és a manifest commit azonosak.
3. A nyomon követett index és worktree nem tartalmaz változtatásokat.
4. A manifest pontosan leírja a várható kerék (wheel) és forrás archívumot.
5. Mindkét artefaktum megegyezik a rögzített bájtméret és SHA-256 hash-vel.
6. A manifest Gitsign és Sigstore validációt követel meg.
7. A Gitsign tanúsítványazonosság (certificate identity) pontosan megegyezik a `RELEASE_COMMIT_IDENTITY`-vel.
8. A Gitsign kiállító (issuer) pontosan megegyezik a `RELEASE_COMMIT_OIDC_ISSUER`-rel.
9. A Gitsign ellenőrzi a Git aláírást, Rekor bejegyzést és tanúsítványigényeket.
10. Mindkét artefaktumnak érvényes SLSA eredet-igazolási tanúsítása van.
11. A tanúsítás repository-ja, workflow-ja, forrás digest-je és forrás referenciája megegyezik a kiadáséval.
12. A tanúsítás predikátuma `https://slsa.dev/provenance/v1`.

**Kötelező repository változók:**

~~~text
RELEASE_COMMIT_IDENTITY
RELEASE_COMMIT_OIDC_ISSUER
~~~

**Kötelező GitHub környezet:**

~~~text
pypi
~~~

**Kötelező PyPI Trusted Publisher leképezés:**

~~~text
Owner:       CONFIRMED_GITHUB_OWNER
Repository:  CONFIRMED_REPOSITORY
Workflow:    release.yml
Environment: pypi
~~~

---
## Validációs bizonyítékok

### Standard repository gate

A legutóbbi `scripts/verify` futtatás sikeres volt:

- Ruff lint: pass
- Ruff format check: pass
- Strict mypy a src és tests mappáknál: pass
- Pytest: 123 sikerült, 1 kihagyott
- Kanonikus validáció: 3 packages
- Dokumentációs link-ek: pass
- Vetítés drift: nincs
- Statikus megfelelőség: 27 ellenőrzés sikeres
- Opcionális külső skills-ref validator: kihagyott, mert nincs telepítve

### Vetítés és csomagolás

- A vetítés dry-run nem jelentett változtatást.
- A vetítés drift ellenőrzés nem jelentett változtatást.
- A kerék (wheel) tartalmazza a teljes generált három-skill vetítést.
- A forrás archívum tartalmazza a vetítést, release workflow-t, release kódot,
  és release dokumentációt.
- Egyik archívum sem tartalmaz generált Python bájtkódot.
- A végső kerék (wheel) sikeresen települt egy eldobható környezetben.
- A telepített kerék dry-run, apply, check és rollback mind sikeres volt a
  beágyazott vetítés használatával.

### Release-mód orchestráció

Egy eldobható írójogos Git repositoryorgt hoztunk létre a következőkkel:

- egy valódí commit-tal;
- egy illeszkedő v0.8.1 tag-gel;
- egy tiszta nyomon követett worktree-vel;
- a helyi kerék (wheel) és forrás archívummal;
- generált kiadási bizonyítékokkal.

A teljes release validációs parancs sikeres volt kontrollált gh és
gitsign verifikátor csatulókkal (stubs). Ez bizonyítja a parancs orchestrációt,
politikák terjesztését, tag és commit ellenőrzéseket, artefaktum validációt,
éss fail-closed kezelést. Külön negatív tesztek bizonyítják, hogy az érvénytelen
verifikátor kilépések elutasítva vannak.

Ez **nem** jelenti valódí Gitsign vagy Sigstore kriptográfiai bizonyítékot.
Csak a konfigurált valódí GitHub release workflow adhat ki és ellenőrizheti
ezt a bizonyítékot.

### Jelenlegi helyi artefaktumok

Kerék (Wheel):

~~~text
dist/polymind_constellation-0.8.1-py3-none-any.whl
SHA-256: 8f01bf2b3427acc198b738b1e3096d3f59bd8b413f31521eee8ede810b9518b9
~~~

Az átadás (handoff) része a forrás archívumnak. Emiatt a digest-je nem ágyazott
ide, mivel ez a dokumentum változtatása megváltoztatja azt az archívumot is.
A hatóságos forrás-archívum digest-je a végső dokumentációs build után generálandó;
a release workflow rögzíti azt a SHA256SUMS és release-manifest.json fájlokban.

A helyi build-elt archívumok validációs artefaktumok. A tag-elt GitHub workflow
kötelezően újraépítenie kell a nyilvános kiadási artefaktumokat a valódí aláírt
commit-ből.

---
## Jelenlegi külső blokkolók

- A munkatér `.git` elérési útja egy nem működő, csak olvasható helykitöltő (placeholder).
- Nincs használható branch, előzmény, tag, vagy távoli metaadatok elérhetők itten.
- A konfigurált w7-mgfcode GitHub hitelesítő érvénytelen.
- A konfigurált llw7-hector GitHub hitelesítő érvénytelen.
- A szándékozott GitHub tulajdonos/repository azonosítás megerősítetlen.
- A pypi GitHub környezet nincs konfigurálva.
- A PyPI Trusted Publisher leképezés nincs konfigurálva.
- A `RELEASE_COMMIT_IDENTITY` nincs konfigurálva.
- A `RELEASE_COMMIT_OIDC_ISSUER` nincs konfigurálva.
- Nincs valódí Gitsign-aláírt release commit ebben a munkatérben.
- Nincs GitHub által kiállított artefaktum tanúsítás.
- A 0.8.1 csomag és GitHub Release nem került még közzétételre.

**Ne kerüljön meg ezek a blokkolók** helyi Twine feltöltéssel, aláíratlan tag-gel,
ellenőrizetlen azonosítással, vagy kézi cserevel!

---
## Jelen munkamenet fájljai

~~~text
.github/dependabot.yml
.github/workflows/ci.yml
.github/workflows/release.yml
.gitignore
CHANGELOG.md
CONTRIBUTING.md
HANDOFF.md
README.md
docs/development-directions.md
docs/phase8-release.md
docs/phase9-registry.md
docs/prioritized-todo.md
docs/release-automation.md
docs/security.md
docs/versioning.md
src/polymind/cli.py
src/polymind/installer.py
src/polymind/projection.py
src/polymind/release.py
src/polymind/validation.py
src/polymind/verify.py
tests/test_conformance.py
tests/test_installer.py
tests/test_projection.py
tests/test_provenance.py
tests/test_release.py
~~~

A `dist/repo` alatti generált vetületek validáltak, de generált, csak olvasható
artefaktumok maradnak.

---
## Holttérutak és megoldások

- **Repository ellenőrzés meghiúsult:** A Git parancsok a munkatér ellen meghiúsultak,
  mert a `.git` csak egy védett helykitöltő. A megoldás egy valódí klón igényel;
  nincs szintetikus előzmény (history) a munkatérben.
- **GitHub műveletek meghiúsultak:** Mindkét konfigurált GitHub hitelesítő érvénytelen.
  A megoldás interaktív újra-autentikációt igényel a repository tulajdonostól.
- **Első izolált build meghiúsult:** A homokozó (sandbox) nem tudta feloldani a Hatchling
  build backend-et. A hitelesített build-t újra futtattuk külső függőség hozzáféréssel,
  és sikeres volt.
- **Valódí eredet-igazolás nem készíthető helyben:** GitHub OIDC, Sigstore
  tanúsítás kiállítása, és a valódí aláírói azonosítás nem elérhető.
  Eldobható csatolókat (stubs) használtunk kizárólag az orchestráció validálásához;
  ez a korlátítás kifejezetten rögzített.
- **Közvetlen kézi közzététel elutasítva mint munkaaround:** Ez kikerülné a
  kiválasztott Trusted Publishing és eredet-igazolási kontrollokat.

---
## Nyitott kérdések

- Mi a hatóságos GitHub tulajdonos/repository?
- Melyik GitHub fiók birtokolja és adminisztrálja a kiadást?
- Mi a pontos Gitsign tanúsítványazonosság (certificate identity), ami engedélyezett?
- Mi a pontos OIDC kiállító (issuer), ami engedélyezett?
- Támogatja-e a repository terv a szükséges artefaktum-tanúsítási funkciókat?
- Kellene-e, hogy a munkamenet-átadások (session-handoffs) kanonikus Polymind csomaggá váljanak,
  vagy maradjanak külsőek?
- A közzététel után, melyik élő megfelelőségi rést kell először kezelni:
  Claude meghívás, OpenCode felfedezés, vagy cross-provider jóváhagyási paritás?

---
## Prioritásos következő lépések

A teljes függőség-alapú ellenőrzési lista és elfogadási kritériumok a
[prioritized-todo.md](../prioritized-todo.md) fájlban találhatók. A kritikus út:

~~~text
RESTORE_GIT
-> AUTHENTICATE_GITHUB
-> CONFIGURE_GITSIGN
-> CONFIGURE_PYPI_OIDC
-> VALIDATE_REAL_WORKFLOW
-> ADD_RELEASE_RECOVERY
-> SIGN_AND_TAG_0.8.1
-> PUBLISH
-> INDEPENDENTLY_VERIFY
-> CLOSE_RELEASE
~~~

Azonnali akciók:

1. Állítsd vissza egy írójogos klónját a hatóságos GitHub repository-nak.
2. Űzd meg és add át a teljes jelenlegi munkatéri állapotot.
3. Erősítsd meg a tulajdonos/repository-t és az alapértelmezett branch-öt.
4. Autentikáld újra a helyes GitHub fiókot.
5. Konfiguráld a Gitsign azonosítást és issuer repository változókat.
6. Hozd létre a védett pypi környezetet és a PyPI Trusted Publisher leképezést.
7. Validáld a workflow-öket egy pull requestben anélkül, hogy közzétennéd.
8. Implementáld és teszteld a részleges-kiadás helyreállítási utat.
9. Írd alá a végső release commit-ot, ellenőrizd, és hozd létre a v0.8.1 tag-et.
10. Tolja fel a tag-et, és hagy'd, hogy a workflow build-eljen, tanúsítson, közzétegyen és kiadjon.
11. Töltsd le függetlenül és ellenőrizd a közzétett artefaktumokat.
12. Frissítsd a kiadási rekordot a helyi validáltról közzétettre.

---
## Parancsok a következő munkamenethez

A valódí repository visszaállítás után:

~~~sh
gh auth status
git status
git remote -v
git branch --show-current
git ls-remote --tags origin v0.8.1

scripts/sync-adapters --dry-run
scripts/sync-adapters --check
scripts/verify

gitsign verify \
  --certificate-identity="$RELEASE_COMMIT_IDENTITY" \
  --certificate-oidc-issuer="$RELEASE_COMMIT_OIDC_ISSUER" \
  HEAD

git diff --quiet
git diff --cached --quiet
git rev-parse HEAD
git rev-parse 'refs/tags/v0.8.1^{commit}'
~~~

**Ne toljad fel a v0.8.1-et amíg a GitHub autentikáció, a Gitsign változók, a pypi környezet,
a PyPI Trusted Publisher és a részleges-kiadás helyreállítás nem validáltak!**

---
## Repository szabályok megőrzése

- Csak a `skills/` alatti kanonikus csomagokat szerkesztd kézi módon.
- A `dist/repo/.agents/skills` és `dist/repo/.claude/skills` generált és csak olvasható.
- A csomagok önállóan kezelhetők legyenek.
- A provider engedélyek ne legyenek a kanonikus SKILL.md fájlokban.
- A shell wrapper-ek legyenek vékonyak; az implementáció a `src/polymind/` könyvtárban legyen.
- Minden új validációs szabályhoz adj hozzá tesztet, és tartsd stabilon a diagnosztikai kódokat.
- Az ismeretlen képességek, elérési út szökések (path escapes), szimbolikus link-ek és vetítési ütközések
  zárjanak le *fail-closed* módon.
- Soha ne írj fel független vagy nem generált leáramlási tartalmat.
