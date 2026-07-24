# Át Rangsorolt TODO Lista

Dátum: 2026-07-23

---
## Rangsorolási módszer

- **Prioritási pontszám:** kiadási hatás 35%, biztonság és kockázat csökkentés 25%,
  függőségi érték 20%, és felhasználói érték 20%.
- **Komplexitás:** 1 = triviális, 5 = nagy architektonikai munka.
- A feladatok prioritás, függőségek, majd komplexitás szerint vannak rendeelve.

---
## Rangsorolt backlog

| Rang | Feladat | Prioritás | Pont | Komplexitás | Független |
| ---: | --- | --- | ---: | ---: | --- |
| 1 | A valódí Git repository visszaállítása | P0 | 100 | 2 | — |
| 2 | GitHub tulajdonosság megerősítése és újra-autentikáció | P0 | 98 | 1 | 1 |
| 3 | Gitsign kiadási azonosítás konfigurálása | P0 | 96 | 3 | 1-2 |
| 4 | PyPI Trusted Publishing konfigurálása | P0 | 95 | 2 | 2 |
| 5 | A release workflow validálása a valódí repository-ban | P0 | 94 | 3 | 1-4 |
| 6 | Részleges-kiadás helyreállítási eljárás hozzáadása | P0 | 92 | 3 | 5 |
| 7 | A végső 0.8.1 commit és tag aláírása, létrehozása | P0 | 91 | 2 | 1-6 |
| 8 | 0.8.1 közzététele GitHub Actions-en keresztül | P0 | 90 | 2 | 7 |
| 9 | A közzétett kiadás független ellenőrzése | P0 | 89 | 2 | 8 |
| 10 | A 0.8.1 kiadási ciklus lezárása és rögzítése | P1 | 82 | 1 | 9 |
| 11 | Kiadási kormányzás (governance) és workflow linting megerősítése | P1 | 78 | 3 | 5 |
| 12 | Eredet-igazolás (provenance) SLSA Build Level 3 felé fejlesztése | P2 | 66 | 5 | 8-11 |
| 13 | A 9. fázis registry fenyegetési modelljének és ADR-jének írása | P2 | 61 | 3 | 10 |
| 14 | OCI skill artefaktum szerződés meghatározása | P2 | 59 | 3 | 13 |
| 15 | Eldobható OCI registry fixture építése | P2 | 56 | 4 | 14 |
| 16 | Polymind registry publish implementálása | P2 | 53 | 5 | 14-15 |
| 17 | Digest-pinned registry letöltések implementálása | P2 | 51 | 5 | 15-16 |
| 18 | Registry autentikáció és RBAC tesztek hozzáadása | P2 | 49 | 5 | 16-17 |
| 19 | Registry integrálása a catalog.py-be | P3 | 43 | 5 | 17-18 |
| 20 | Maradék provider élő-megfelelőségi (live-conformance) rések bezárása | P3 | 39 | 5 | 10 |

---
## P0 - Kiadás-blokkoló munka

### TODO 1: Funkcionális Git repository visszaállítása

**Komplexitás:** 2/5
**Felelős:** Repository adminisztrátor

- [ ] Azonosítsd a hatóságos GitHub repository-t.
- [ ] Erősítsd meg a pontos tulajdonos/repository azonosítást.
- [ ] Klónozd le egy írójogos munkakönyvtárba.
- [ ] Add át a jelenlegi munkatéri változtatásokat anélkül, hogy felülírnád a nem kapcsolódó munkát.
- [ ] Győződj meg arról, hogy a `.git` érvényes repository metaadatokat tartalmaz.
- [ ] Ellenőrizd az alapértelmezett branch-öt és a konfigurált remote-okat.
- [ ] Vizsgáld meg a branch-eket, tag-eket, kiadási előzményeket és a függő remote változtatásokat.
- [ ] Győződj meg arról, hogy a v0.8.1 nem létezik sem helyben, sem távolon.
- [ ] Tekintsd át a teljes átvitt diff-et.
- [ ] Győződj meg arról, hogy a generált kiadási bizonyítékok továbbra is ignoráltak maradnak.

**Elfogadási kritériumok:**

~~~sh
git status
git remote -v
git branch --show-current
git ls-remote --tags origin v0.8.1
~~~

Minden parancsnak sikeresnek kell lennie, és a v0.8.1-nek nem szabad ütközni egy meglévő tag-gel vagy kiadással.

---
### TODO 2: GitHub autentikáció visszaállítása

**Komplexitás:** 1/5
**Függ:** TODO 1

- [ ] Válaszd ki a helyes GitHub fiókot.
- [ ] Futtasd a `gh auth login -h github.com` parancsot.
- [ ] Erősítsd meg, hogy a fióknak van repository adminisztrációs jogai.
- [ ] Erősítsd meg a jogot az Actions, környezetek, változók, kiadások, szabályok és tag-ek kezeléséhez.
- [ ] Erősítsd meg, hogy az artefaktum tanúsítások elérhetők a repository-nak és a tervnek.
- [ ] Erősítsd meg, hogy a GitHub CLI az Actions-ben támogatja a `gh attestation verify` parancsot.

**Elfogadási kritériumok:**

~~~sh
gh auth status
gh repo view OWNER/REPOSITORY
gh workflow list --repo OWNER/REPOSITORY
~~~

---
### TODO 3: Gitsign kiadási azonosítás konfigurálása

**Komplexitás:** 3/5
**Függ:** TODOs 1-2

- [ ] Válaszd ki a hatóságos kiadási aláírói azonosítást.
- [ ] Válaszd ki az elfogadott OIDC kiállítót (issuer).
- [ ] Dokumentezd, hogy az azonosítás e-mail cím vagy URI.
- [ ] Konfiguráld a Gitsign-t helyben.
- [ ] Állítsd be a repository `RELEASE_COMMIT_IDENTITY` változóját.
- [ ] Állítsd be a repository `RELEASE_COMMIT_OIDC_ISSUER` változóját.
- [ ] Győződj meg arról, hogy mindkét érték pontosan megegyezik a Gitsign tanúsítvány igényével.
- [ ] Írd alá egy nem-kiadási teszt commit-ot.
- [ ] Ellenőrizd a release gate pontos azonosítási argumentumaival.
- [ ] Erősítsd meg a Git aláírás, Rekor bejegyzés és tanúsítvány-igény validációt.
- [ ] Dokumentezd az aláírói forgatást és a vészes visszavonást.

**Elfogadási kritériumok:**

~~~sh
gitsign verify \
  --certificate-identity="$RELEASE_COMMIT_IDENTITY" \
  --certificate-oidc-issuer="$RELEASE_COMMIT_OIDC_ISSUER" \
  HEAD
~~~

---
### TODO 4: PyPI Trusted Publishing konfigurálása

**Komplexitás:** 2/5
**Függ:** TODO 2

- [ ] Erősítsd meg, hogy a `polymind-constellation` már létezik-e a PyPI-n.
- [ ] Hozz létre egy függőben lévő kiadót, ha ez az első közzététel.
- [ ] Hozd létre a `pypi` nevű GitHub környezetet.
- [ ] Adj hozzá szükséges felülvizsgálókat, ahol támogatott.
- [ ] Korlátozd a környezetet védett verzió tag-ekre.
- [ ] Konfiguráld a pontos Trusted Publisher leképezést:

~~~text
Owner:       CONFIRMED_GITHUB_OWNER
Repository:  CONFIRMED_REPOSITORY
Workflow:    release.yml
Environment: pypi
~~~

- [ ] Erősítsd meg, hogy nincsen `PYPI_TOKEN`, `TWINE_PASSWORD`, vagy hosszú életű hitelesítő tárolva.
- [ ] Erősítsd meg, hogy a publish job-nak csak `contents: read` és `id-token: write` engedélyei vannak.

**Elfogadási kritérium:** A PyPI leképezés és GitHub környezet **pontosan** meg kell egyezzen a workflow konfigurációval.

---
### TODO 5: Workflow validálása a valódí repository-ban

**Komplexitás:** 3/5
**Függ:** TODOs 1-4

- [ ] Add hozzá a megvalósított CI és release workflow-öket a valódí repository-ba.
- [ ] Erősítsd meg, hogy minden harmadik féltől származó action 40 karakteres commit SHA-hoz van rögzítve.
- [ ] Validáld a workflow YAML-t az `actionlint`-tel.
- [ ] Erősítsd meg, hogy a release végrehajtás korlátozva van verzió tag-ekre.
- [ ] Erősítsd meg, hogy egy helytelen tag hibát okoz a `polymind release-manifest`-ben.
- [ ] Erősítsd meg, hogy a hiányzó Gitsign változók *fail-closed* módon hibát okoznak.
- [ ] Erősítsd meg, hogy a hiányzó attestation bundle *fail-closed* módon hibát okoz.
- [ ] Erősítsd meg, hogy egy aláíratlan release commit elutasítva van.
- [ ] Erősítsd meg, hogy egy nem egyező aláírói azonosítás vagy kiállító elutasítva van.
- [ ] Erősítsd meg, hogy a nem egyező tag, commit, repository, workflow, ref és digest értékek elutasítva vannak.
- [ ] Erősítsd meg, hogy a pull request-ek nem kaphatnak közzétételi engedélyeket.

**Elfogadási kritériumok:** A CI sikeres egy normál pull request-nél, nem történik közzététel, és minden negatív release forgatókönyv hibát okoz a szándékozott gate-nél.

---
### TODO 6: Részleges-kiadás helyreállítás hozzáadása

**Komplexitás:** 3/5
**Függ:** TODO 5

A jelenlegi workflow a GitHub Release-t hozza létre a PyPI siker után. Egy későbbi GitHub hiba nem kényszeríthet egy biztonságtalan PyPI újra-feltöltést.

- [ ] Definiáld a helyreállítást a *"PyPI sikerült, GitHub Release meghiúsult"* helyzetre.
- [ ] Tartsd meg a disztribúciókat és bizonyítékokat elég hosszú ideig a helyreállításhoz.
- [ ] Adj hozzá egy finalize-only workflow-t vagy egy dokumentált karbantartói parancsot.
- [ ] Ellenőrizd a meglévő PyPI digest-eket a SHA256SUMS ellen a finalizálás előtt.
- [ ] Akadályozd meg a helyreállítást, hogy újra építsen vagy cseréljen artefaktumokat.
- [ ] Akadályozd meg, hogy a `skip-existing` elfogadja a nem egyező PyPI fájlokat csendben.
- [ ] Szimuláld egy GitHub Release hibáját a sikeres közzététel után.
- [ ] Teszteld a teljes helyreállítási utat.
- [ ] Dokumentezd a biztonságos és biztonságtalan újrapróbálásokat.
- [ ] Dokumentezd a PyPI fájlnév változtathatatlanságát.

**Elfogadási kritérium:** Egy meghiúsult GitHub Release lépés folytatható anélkül, hogy újra építené vagy közzétenné a PyPI artefaktumokat.

---
### TODO 7: A végső release commit és tag előkészítése

**Komplexitás:** 2/5
**Függ:** TODOs 1-6

- [ ] Alkalmazd a felülvizsgált munkatéri változtatásokat a valódí repository-ban.
- [ ] Erősítsd meg a verzió konzisztenciáját a `pyproject.toml`, `uv.lock`,
  `polymind.__version__`, `projection.lock.json` és `CHANGELOG.md` között.
- [ ] Futtasd a vetítés dry-run és drift ellenőrzéseket.
- [ ] Futtasd a teljes validációs szvitet.
- [ ] Tekintsd át a teljes Git diff-et.
- [ ] Commit-old csak a szándékozott 0.8.1 változtatásokat.
- [ ] Írd alá a release commit-ot a Gitsign-nel.
- [ ] Ellenőrizd a pontos tanúsítványazonosságot és kiállítót.
- [ ] Győződj meg arról, hogy a nyomon követett worktree és index tiszta.
- [ ] Hozd létre a pontos `v0.8.1` tag-et.
- [ ] Ellenőrizd, hogy a tag a signed release commit-ra mutat.

**Elfogadási kritériumok:**

~~~sh
scripts/sync-adapters --dry-run
scripts/sync-adapters --check
scripts/verify
git diff --quiet
git diff --cached --quiet
gitsign verify ... HEAD
git rev-parse HEAD
git rev-parse 'refs/tags/v0.8.1^{commit}'
~~~

A végső két commit értéknek **azonosnak** kell lennie.

---
### TODO 8: 0.8.1 közzététele

**Komplexitás:** 2/5
**Függ:** TODO 7

- [ ] Tolja fel a release commit-ot.
- [ ] Várj a szükséges CI ellenőrzésekre.
- [ ] Tolja fel **csak** a `v0.8.1` tag-et.
- [ ] Kövesd a Release workflow-t.
- [ ] Erősítsd meg, hogy a forrás validáció sikeres.
- [ ] Erősítsd meg, hogy friss kerék (wheel) és sdist építés történik.
- [ ] Erősítsd meg a SHA-256 bizonyíték generálását.
- [ ] Erősítsd meg a közvetlen Gitsign commit validációt.
- [ ] Erősítsd meg a GitHub/Sigstore artefaktum tanúsítás generálását.
- [ ] Erősítsd meg, hogy mindkét artefaktum átmegy a `gh attestation verify` ellenőrzésen.
- [ ] Fogadd el a védett pypi deployment-ot.
- [ ] Erősítsd meg a PyPI közzétételt.
- [ ] Erősítsd meg a GitHub Release létrehozását.
- [ ] **Ne** tölts fel kézi módon helyben épített validációs artefaktumokat.

---
### TODO 9: A nyilvános kiadás független ellenőrzése

**Komplexitás:** 2/5
**Függ:** TODO 8

- [ ] Töltsd le a kerék (wheel) és sdist fájlokat a PyPI-ről.
- [ ] Töltsd le az összes GitHub Release asset-et.
- [ ] Hasonlítsd össze a fájlneveket, méreteket és SHA-256 értékeket.
- [ ] Ellenőrizd mindkét Sigstore tanúsítást függetlenül.
- [ ] Erősítsd meg, hogy a forrás digest megegyezik a release commit-tal.
- [ ] Erősítsd meg, hogy a forrás ref `refs/tags/v0.8.1`.
- [ ] Erősítsd meg a pontos aláíró workflow-t.
- [ ] Telepítsd a letöltött PyPI kerék (wheel) fájlt egy eldobható környezetben.
- [ ] Futtasd a telepítő dry-run, apply, check és rollback parancsokat.
- [ ] Erősítsd meg, hogy a kerék (wheel) nem tartalmaz generált bájtkódot.
- [ ] Erősítsd meg, hogy a PyPI és GitHub bájtonként azonos disztribúciókat szolgáltat.

**Elfogadási kritérium:** Mindkét registry azonos artefaktumokat készít érvényes forrás- és build eredet-igazolással.

---
---
## P1 - Kiadási lezárás és kormányzás

### TODO 10: Kiadási ciklus lezárása

**Komplexitás:** 1/5
**Függ:** TODO 9

- [ ] Változtasd meg a kiadási dokumentációt "helyben validált"-ról "közzétett"-re.
- [ ] Rögzítsd a PyPI és GitHub Release URL-eket.
- [ ] Rögzítsd a tag-et, commit-ot, workflow futtatást, fájlneveket, méreteket és digest-eket.
- [ ] Frissítsd a `HANDOFF.md` fájlt.
- [ ] Frissítsd a 8. fázis kiadási rekordot.
- [ ] Rögzítsd a szándékos validációs kihagyásokat külön a sikeres validációktól.
- [ ] Rögzítsd a Gitsign azonosítást és kiállítót hitelesítő adatok nélkül.
- [ ] Hozz létre követő issue-öket a figyelmeztetések vagy kézi beavatkozások számára.

---
### TODO 11: Kiadási kormányzás (governance) megerősítése

**Komplexitás:** 3/5
**Függ:** TODO 5

- [ ] Adj hozzá `actionlint`-et a helyi és CI validációhoz.
- [ ] Adj hozzá CODEOWNERS fedészőt a workflow-ök, eredet-igazolási kód és kiadási dokumentációhoz.
- [ ] Védd az alapértelmezett branch-öt.
- [ ] Korlátozd a verzió-tag létrehozást.
- [ ] Követsd el az aláírt commit-okat a kiadás előkészítésénél, ahol lehetséges.
- [ ] Kövessed el a CI-t a merge előtt.
- [ ] Adj hozzá környezeti felülvizsgálókat a PyPI közzétételhez.
- [ ] Definiáld a Gitsign azonosítás forgatását.
- [ ] Definiáld a Gitsign bináris frissítés és checksum-felülvizsgálati folyamatot.
- [ ] Teszteld a minimális jogok elvét minden job-nál.
- [ ] Adj hozzá időzített eredet-igazolási ellenőrzési füsttesztet.

---
---
## P2 - Eredet-igazolási érettség és registry alapozás

### TODO 12: SLSA Build Level 3 felé fejlesztés

**Komplexitás:** 5/5
**Függ:** TODOs 8-11

- [ ] Mozgassd a build-et és tanúsítás generálást egy újrahasznosítható workflow-ba.
- [ ] Akadályozd meg, hogy a hívók megváltoztassák a biztonságkritikus build lépéseket.
- [ ] Válaszd szét a nem megbízható hívói input-okat a builder-től.
- [ ] Rögzítsd az újrahasznosítható workflow-t változtathatlan commit SHA-val.
- [ ] Validáld az aláíró repository-t és workflow azonosítást.
- [ ] Utasítsd el a self-hosted runner-öket, ahol alkalmazható.
- [ ] Készíts egy hivatalos SLSA szintű értékelést.
- [ ] **Ne** igényelj Level 3-at amíg minden követelmény függetlenül felül nem vizsgált.

---
### TODO 13: Registry fenyegetési modell és ADR írása

**Komplexitás:** 3/5
**Függ:** TODO 10

- [ ] Definiáld a kiadó, registry, fogyasztó és katalógus bizalmi határait.
- [ ] Fedd le a felülírás, replay, lejtmenet (downgrade), namespace-squatting és digest-confusion fenyegetéseket.
- [ ] Definiáld a *fail-closed* viselkedést a hiányzó eredet-igazolás esetén.
- [ ] Hasonlítsd össze a GHCR-t, egy másik OCI registry-t és egyéni objektum tárolást.
- [ ] Rögzítsd az OCI/ORAS backend döntést.
- [ ] Definiáld a megtartási, elavulási és törlési politikákat.
- [ ] Definiáld a helyreállítást egy kompromittált kiadó esetében.

---
### TODO 14: OCI skill artefaktum szerződés meghatározása

**Komplexitás:** 3/5
**Függ:** TODO 13

- [ ] Finalizáld az artefaktum és manifest MIME típusokat.
- [ ] Definiáld a determinisztikus skill archívum építést.
- [ ] Definiáld a szükséges OCI annotációkat.
- [ ] Definiáld a SemVer tag viselkedést és felülírás elutasítást.
- [ ] Követsd el a digest-pinned telepítést.
- [ ] Definiáld az eredet-igazolási és aláírási referenseket.
- [ ] Definiáld a framework kompatibilitási metaadatokat.
- [ ] Definiáld a képesség nyilatkozatokat és validációs szabályokat.
- [ ] Közzétegy érvényes példákat és érvénytelen fixture-eket.

---
### TODO 15: Eldobható registry fixture építése

**Komplexitás:** 4/5
**Függ:** TODO 14

- [ ] Adj hozzá egy helyi OCI Distribution registry fixture-t.
- [ ] Tolj fel és tölts le egy minimális skill-t ORAS-on keresztül.
- [ ] Teszteld a manifest és blob digest validációt.
- [ ] Teszteld a változtathatatlan verzió kényszerítést.
- [ ] Teszteld a hiányzó és hibás eredet-igazolást.
- [ ] Teszteld az ismeretlen MIME típusokat és namespace ütközéseket.
- [ ] Győződj meg arról, hogy a teszteknél nincsenek szükség termelési hitelesítőkre.

---
### TODO 16: Polymind registry publish implementálása

**Komplexitás:** 5/5
**Függ:** TODOs 14-15

- [ ] Validáld a kanonikus csomagot a csomagolás előtt.
- [ ] Készíts egy determinisztikus archívumot.
- [ ] Számítsd ki az archívum és manifest digest-jeit.
- [ ] Autentikáld anélkül, hogy parancssori hitelesítőket használnál.
- [ ] Utasítsd el egy meglévő SemVer tag-et más digest-tel.
- [ ] Tolj fel blob-okat és manifest-eket ORAS-on keresztül.
- [ ] Csatolj eredet-igazolást.
- [ ] Ellenőrizd a távoli digest-et a közzététel után.
- [ ] Alapértelmezésként használj dry-run-t.
- [ ] Adj hozzá átfogó negatív teszteket.

---
### TODO 17: Digest-pinned letöltések implementálása

**Komplexitás:** 5/5
**Függ:** TODOs 15-16

- [ ] Oldd fel a nevet és verziót egy változtathatatlan digest-re.
- [ ] Töltsd le egy korlátozott ideiglenes könyvtárba.
- [ ] Érvényesítsd a méret és fájl-szám korlátokat.
- [ ] Utasítsd el a szimbolikus link-eket és elérési út traversal-öket.
- [ ] Ellenőrizd az OCI manifest és blob digest-eket.
- [ ] Ellenőrizd a Sigstore eredet-igazolást.
- [ ] Futtasd a kanonikus csomag validátort.
- [ ] Gyorsítótárazd csak a digest-alapú validált tartalmat.
- [ ] Utasítsd el a változó vagy digest nélküli kéréseket szigorú politika alatt.

---
### TODO 18: Registry autentikáció és RBAC tesztek hozzáadása

**Komplexitás:** 5/5
**Függ:** TODOs 16-17

- [ ] Definiáld az olvasó, kiadó, karbantartó és adminisztrátor szerepeket.
- [ ] Teszteld a nem engedélyezett push és pull műveleteket.
- [ ] Teszteld a cross-namespace közzététel tagadását.
- [ ] Teszteld a kiadó visszavonását és token lejáratát.
- [ ] Teszteld a hitelesítő adatok redaction-ét a naplókban.
- [ ] Dokumentezd az interaktív és CI autentikációt.
- [ ] Tartsd a provider hitelesítőket a kanonikus skill csomagokon kívül.

---
---
## P3 - Szélesebb integráció

### TODO 19: Registry integrálása a catalog.py-be

**Komplexitás:** 5/5
**Függ:** TODOs 17-18

- [ ] Tartsd meg a jelenlegi helyi, csak adatokra vonatkozó katalógus viselkedést.
- [ ] Adj hozzá explicit registry konfigurációt.
- [ ] Válaszd szét a keresést, feloldást, letöltést, validációt és aktiválást.
- [ ] **Soha** ne futtass le letöltött csomagkódot.
- [ ] Tedd elérhetővé a forrás, verzió, digest és eredet-igazolási állapotot.
- [ ] Követsd el az explicit hálózati jóváhagyást, ahol alkalmazható.
- [ ] Adj hozzá offline és korrupt cache viselkedést.
- [ ] Adj hozzá determinisztikus katalógus snapshot-okat.

---
### TODO 20: Maradék provider élő-megfelelőségi (live-conformance) rések bezárása

**Komplexitás:** 5/5
**Függ:** TODO 10

- [ ] Futtass egy valódí Claude élő meghívást.
- [ ] Validáld az OpenCode natív helyi-modell felfedezést.
- [ ] Teszteld a pozitív és negatív trigger-eket minden támogatott provider-nél.
- [ ] Teszteld az erőforrás betöltést, jóváhagyási stop-pokokat és jogok szűkítését.
- [ ] Rögzítsd a nem elérhető runtime-okat "skip"-ként.
- [ ] Frissítsd a kompatibilitási bizonyíték mátrixot.
- [ ] Tartsd meg a különböző statikus, mért, részleges, kihagyott és sikeres állapotokat.

---
## Kritikus végrehajtási út

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

**Kapcsolódó dokumentumok:**

- [Fejlesztési irány döntés](../development-directions.md)
- [Kiadásautomatizálás és eredet-igazolás](../release-automation.md)
- [9. fázis registry közzétételi terv](../phase9-registry.md)
- [Verziózás és kiadási politika](../versioning.md)
