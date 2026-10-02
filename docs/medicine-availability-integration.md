# Medicine Availability Router - childofanandroid.co.uk integration guide

Status: implementation guide only  
Research date: 2 October 2026  
Public launch status: **blocked pending data-rights, medicines-advertising and privacy gates**

The canonical research/architecture owner is ICHARIS2:

https://github.com/ChildOfAnAndroid/icharis2/blob/main/docs/architecture/medicine_availability_router.md

This website must remain a presentation/proxy layer. It must not become the owner of medicine, pharmacy or stock truth.

## 1. Existing website architecture

Current source already has the right basic shape for a public read surface:

- Vue 3 + TypeScript;
- Vite;
- Vue Router;
- same-origin frontend API helper in src/api.ts;
- Flask backend in PYTHON/bbyServer.py;
- /api development proxy in vite.config.ts;
- backend bound to loopback by default and deployed behind the existing reverse proxy;
- explicit write-origin restrictions and owner-only auth for privileged gallery operations.

The availability feature should reuse these surfaces rather than introduce a second frontend framework or a browser-side direct connection to pharmacy/vendor APIs.

## 2. Ownership boundary

Canonical truth:

    ICHARIS2 availability service
      medicine identity
      pharmacy identity
      source semantics
      availability observations
      source health
      national supply context

Website responsibility:

    childofanandroid.co.uk
      collect one ephemeral search request
      send it to a same-origin API route
      render the returned projection
      explain evidence quality/staleness
      never persist private search history by default

Forbidden duplication:

- no website-local stock database;
- no website-side polling of Boots, PMRs or wholesalers;
- no browser-exposed vendor credentials;
- no duplicated medicine identity model;
- no separate website source-health logic;
- no query-history analytics containing medicine + location.

## 3. Recommended production topology

Preferred shape:

    browser
      |
      v
    childofanandroid.co.uk
      |
      +-- existing /api/* -> Flask/BabyLLM owner
      |
      +-- /api/medicine-availability/*
             |
             v
         loopback-only ICHARIS2 availability read service
             |
             v
         canonical availability store/projection

The ICHARIS2 service should bind only to loopback or another private transport selected by the deployment owner.

Two implementation options are valid.

### Option A - reverse proxy directly to ICHARIS2

Route only /api/medicine-availability/* to the ICHARIS2 availability service.

Advantages:
- fewer application hops;
- website Flask code remains unrelated to availability;
- clearer runtime ownership.

Disadvantages:
- reverse-proxy configuration must carry the privacy/no-store headers correctly;
- deployment owner must supervise an additional local service.

### Option B - Flask thin proxy

Add read-only routes to PYTHON/bbyServer.py that forward to the loopback ICHARIS2 service.

Advantages:
- preserves one public API origin/backend entry point;
- easier reuse of existing Flask response hardening and error handling.

Disadvantages:
- must remain a true proxy;
- risk of accidentally adding website-local medicine logic.

Do not read the ICHARIS2 SQLite file directly from the website process.

## 4. Frontend route

Add:

    /medicine-availability

Expected router change:

    import MedicineAvailability from '@/pages/MedicineAvailability.vue'

and one normal named-view route using the existing main/nav layout.

Do not replace the global navigation or visual language just for this feature.

## 5. API helper

Extend src/api.ts with typed calls.

Suggested public types:

    export type AvailabilityState =
      | 'confirmed_fillable'
      | 'on_hand_signal'
      | 'chain_indicated'
      | 'orderable'
      | 'out_of_stock'
      | 'unknown'
      | 'stale'
      | 'source_unavailable'

    export interface MedicineSearchItem {
      concept_id: string
      label: string
      strength?: string
      form?: string
      brand?: string
      pack?: string
    }

    export interface MedicineAvailabilitySearch {
      medicine_concept_id: string
      postcode?: string
      radius_miles?: number
      requested_pack?: string | null
    }

Methods:

    searchMedicines(body)
    searchMedicineAvailability(body)
    getMedicineAvailabilitySourceStatus()

Use POST for both medicine lookup and availability search unless the privacy review proves a GET endpoint is acceptable. Avoid putting medicine names/concept IDs and postcodes in browser URLs, referrers and routine access-log query strings.

## 6. Page component

Suggested files:

    src/pages/MedicineAvailability.vue
    src/components/medicineAvailability/MedicinePicker.vue
    src/components/medicineAvailability/LocationPicker.vue
    src/components/medicineAvailability/AvailabilityResult.vue
    src/components/medicineAvailability/SourceLegend.vue
    src/components/medicineAvailability/NationalSupplyContext.vue

Do not build all components merely because they are listed here. Start with one page and extract components only when the implementation becomes meaningfully clearer.

## 7. User journey

### Step 1 - exact prescription item

The page asks for the medicine as written on the prescription.

Autocomplete returns canonical dm+d-backed candidates.

The UI must make clinically/dispensing-relevant distinctions obvious:
- brand;
- strength;
- form;
- modified-release variant;
- pack where relevant.

Do not silently pick the first fuzzy match.

### Step 2 - area

Accept:
- postcode;
- radius.

No account should be required for v1.

Do not persist the location or medicine search by default.

### Step 3 - results

Render a list first.

A map may be added later, but the complete function must work without one.

Each result shows:
- pharmacy name;
- distance;
- phone/public contact route;
- evidence state;
- human-readable explanation;
- observed time;
- expiry/staleness when relevant;
- source category;
- reservation status;
- separate orderability signal if present.

### Step 4 - national context

National shortage/SSP context lives below or beside the local result list.

Never use a national notice to colour a branch as "out of stock".

## 8. Copy rules

Do not use one generic green "IN STOCK" label.

Preferred labels:

| State | Public label |
| --- | --- |
| confirmed_fillable | Pharmacy confirmed it can fill this |
| on_hand_signal | Direct stock feed saw this item |
| chain_indicated | Chain checker indicates availability |
| orderable | Supplier indicates this can be ordered |
| out_of_stock | Source reports unavailable |
| unknown | No reliable current signal |
| stale | Last signal is too old to rely on |
| source_unavailable | Source temporarily unavailable |

Add a short semantic explanation next to the state.

When the source does not constitute a reservation:

> Availability can change quickly. This is not a reservation. Confirm with the pharmacy before travelling.

The page must not:
- tell a user which prescription medicine is medically preferable;
- recommend switching brand/strength;
- advertise efficacy;
- rank prescription medicines;
- rank pharmacies because they paid;
- use urgency/scarcity language to push a medicine choice.

## 9. Privacy requirements

A medicine search combined with a location can reveal or strongly suggest health information. Treat the feature as sensitive even if no account exists.

Frontend:
- no localStorage/sessionStorage search history;
- no medicine/postcode in route query parameters;
- no third-party analytics event containing medicine/postcode;
- no advertising pixels on this route;
- clear search reset.

Backend/reverse proxy:
- do not log POST bodies;
- no cache of individual search responses outside the canonical availability cache;
- Cache-Control: no-store;
- Referrer-Policy: no-referrer;
- X-Content-Type-Options: nosniff;
- appropriate CSP/Permissions-Policy review before launch.

If a geocoder is used, prefer a server-side privacy-reviewed service and do not disclose medicine data to the geocoder. Geocode only the location.

## 10. Error states

Public errors must preserve uncertainty.

Examples:

    Upstream data is temporarily unavailable.
    We cannot currently tell whether this pharmacy has the item.

not:

    Out of stock

when a source request failed.

Required UI states:
- no exact medicine selected;
- no pharmacies in requested radius;
- no participating availability source;
- source stale;
- partial source outage;
- all sources unavailable;
- medicine identity ambiguous;
- national context unavailable.

## 11. Source coverage disclosure

The feature needs a visible "How this works / coverage" panel.

At minimum display:
- which source categories are currently active;
- whether independent-pharmacy direct feeds are included;
- whether chain data is indicative;
- whether supplier/orderability data is included;
- timestamp of last healthy update;
- known geographic limits.

Never describe partial source coverage as "UK pharmacy stock".

## 12. Backend proxy contract

If Flask proxying is used, the route should:

1. validate content type and bounded body size;
2. validate allowed request fields;
3. forward only to the configured loopback service;
4. use bounded timeout;
5. return structured upstream status;
6. never retry an uncertain mutation - there should be no mutation here anyway;
7. add no-store/privacy headers;
8. not log the request body;
9. fail closed when the ICHARIS2 service is unavailable.

Environment configuration should contain only the internal availability service base URL/transport and timeout. It must not contain copied medicine/source policy.

## 13. Development mode

Vite already proxies /api to the development Flask backend.

Development should support a fixture mode in the ICHARIS2 availability service that returns:
- direct on-hand;
- chain indication;
- orderable-only;
- stale;
- source outage;
- ambiguous medicine;
- no result.

Do not develop the UI against live pharmacy/vendor APIs.

Fixtures should be synthetic and contain no real patient's search data.

## 14. Tests

### Frontend

Test:
- exact medicine disambiguation;
- POST body shape;
- rendering every state;
- source timestamp;
- stale warning;
- partial source outage;
- no medicine selection;
- no results;
- keyboard navigation;
- semantics visible without colour;
- no sensitive state persisted to localStorage/sessionStorage.

### Backend

Test:
- only expected fields accepted;
- bad/malformed body rejected;
- timeout maps to source_unavailable/503, not out_of_stock;
- no-store and no-referrer headers;
- no upstream URL override from client input;
- no vendor credential leakage;
- request body is not added to application logs.

### Deployment smoke tests

After deployment:
- /medicine-availability renders;
- fixture API reachable;
- other site routes unaffected;
- existing chat/gallery/paint APIs unchanged;
- availability service inaccessible directly from the public internet;
- response headers correct;
- no public logs expose sample medicine/postcode values.

## 15. Launch gates

Do not put a "live stock" feature on the public site until all are true:

- ICHARIS2 canonical availability owner exists and is tested;
- dm+d mapping is exact/fail-closed;
- pharmacy identity is canonical;
- at least one lawful direct non-Boots pharmacy feed is live if independent coverage is claimed;
- every source's redistribution/use permission is documented;
- chain indications are labelled as indications;
- orderability is not represented as on-hand;
- controlled-drug exact quantities are not public;
- privacy/DPIA review complete;
- MHRA/POM advertising review complete;
- stale source behaviour is visible;
- source coverage disclosure is accurate;
- production monitoring uses non-sensitive metrics.

## 16. Deployment ownership

The existing website deployment has two separate artefacts:
- Vite frontend build;
- Flask backend source/runtime.

A frontend publication alone does not update the backend.

When this feature is eventually implemented:
1. merge ICHARIS2 availability owner;
2. deploy/supervise the private ICHARIS2 service;
3. merge website frontend/proxy changes;
4. run website tests and npm build;
5. deploy frontend;
6. deploy/restart Flask only if Flask proxy code changed;
7. verify reverse-proxy routing and privacy headers;
8. run live synthetic smoke tests;
9. only then enable the public navigation link.

No deploy step is authorised by this document alone.

## 17. First public beta wording

Suggested neutral introduction:

> **Find pharmacies with current availability signals for your exact prescription.**
>
> We combine several kinds of evidence. Some pharmacies may provide direct stock information; some chain tools only indicate availability; supplier data may show that a pharmacy can order an item. We show those states separately and tell you when each source was last checked.
>
> This service does not prescribe, recommend treatment, reserve medicine, or guarantee supply. Confirm with the pharmacy before travelling.

This copy still requires medicines-advertising review before publication.

## 18. Research source

Full feasibility, source-rights and ICHARIS2 architecture:

https://github.com/ChildOfAnAndroid/icharis2/blob/main/docs/architecture/medicine_availability_router.md
