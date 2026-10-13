# Pathways initial destination verification

Research date: October 12, 2026 (America/New_York).

## Scope and outcome

Research only. The database was inspected in a read-only transaction. No seeds, models, migrations, or database records were changed. No geocoding, estimated coordinates, Mapbox requests, or field inspections were performed.

The database matches the seeds: ten destinations, all `needs_review`, with null descriptions and destination locations; nine lack websites. The only entrance is Island Ford, still `untested` with `verified_at = NULL`. The nine state-park source records point to a generic directory rather than individual park evidence.

All ten have authoritative identity and descriptive evidence suitable for a proposed content update. None is ready for promotion to `verified` or for production routing. Island Ford has a documented entrance and three documented parking coordinate candidates, ready for route testing and endpoint review. The other nine need a specifically documented visitor entrance/parking coordinate before route testing. General park GPS references below must not be imported as entrances.

"Content ready" below means proposed text can be reviewed against the sources; it does not mean the current database record is publishable. "Location reference" means an official published park GPS point, not a calculated centroid and not a confirmed vehicle entrance. Coordinates are latitude, longitude, WGS84; database points remain longitude first. Decimal formatting does not imply surveyed precision.

## Per-destination findings

### 1. Amicalola Falls

- Existing slug: `amicalola-falls-state-park` (retain).
- Official display name: **Amicalola Falls State Park & Lodge**. The seed omits the lodge portion of the DNR heading.
- Location: near Dawsonville; DNR event address **280 Amicalola Falls State Park Road, Dawsonville, GA 30534**.
- Proposed description: A mountain park centered on a 729-foot waterfall, with walking trails and an approach trail toward Springer Mountain.
- Website: [DNR](https://gastateparks.org/AmicalolaFalls), which links to the [official operator](https://amicalolafallslodge.com/).
- [DNR GPS reference](https://explore.gastateparks.org/info/319833?c=33054546): **34.562652, -84.247627**. Point type is not explicitly an entrance or parking lot; do not assign it to an entrance yet.
- Candidate arrival facility: the public visitor center and its parking. The [operator describes a visitor center opened in 2023](https://amicalolafallslodge.com/visitor-center/). Its site also uses **418 Amicalola Falls State Park Rd** for the lodge and event listings, versus DNR's 280 address. Resolve the exact visitor-center address/point with the operator before selecting a primary endpoint.
- Access: [operator park page](https://amicalolafallslodge.com/georgia-state-park/) currently lists the East Ridge Trail closed for maintenance and daylight access. Visitor-center, falls access, and lodge arrivals should not be conflated.
- Readiness: content ready with full-name correction; entrance/parking remains unresolved.

### 2. Vogel

- Official name: **Vogel State Park**; seed name and Blairsville locality agree with [DNR](https://gastateparks.org/Vogel).
- Visitor address: **405 Vogel State Park Road, Blairsville, GA 30512**, supported by the [official reservation listing](https://gastateparks.reserveamerica.com/camping/vogel-state-park/r/campgroundDetails.do?contractCode=GA&parkId=530201).
- Proposed description: A mountain park at the base of Blood Mountain, with forest trails and historic Civilian Conservation Corps facilities surrounding Lake Trahlyta.
- Published location reference: **34.73194, -83.91694**, from the official reservation listing's GPS information. It is not explicitly identified as public parking or an entrance.
- Candidate arrival: public day-use parking serving the visitor center/trails; confirm a specific point. The [DNR trail map](https://gastateparks.org/sites/default/files/parks/pdf/trailmaps/Vogel_TrailMap.pdf) describes trail access near Cottage 7, which is pedestrian trail access, not a substitute vehicle endpoint.
- Access: the live DNR page reports Lake Trahlyta drained for dam work, with the lake loop and waterfall closed. Other park facilities remain open. The reservation page retains generic swimming/lake activities; the current alert takes precedence for proposed trip content.
- Readiness: identity/content ready, with a prominent dated closure note; entrance coordinate unresolved.

### 3. Tallulah Gorge

- Official name: **Tallulah Gorge State Park**; Tallulah Falls locality agrees with [DNR](https://gastateparks.org/TallulahGorge).
- Visitor address: **338 Jane Hurt Yarn Drive, Tallulah Falls, GA 30573**. The accompanying P.O. Box is mailing information, not a routing address.
- Proposed description: A deep river gorge with rim overlooks, waterfalls, a suspension bridge, and an interpretive center.
- [DNR published location reference and directions](https://explore.gastateparks.org/info/320137?mode=m&s=320137.0.0.5): **34.739750, -83.395233**. Directions identify Jane Hurt Yarn Drive and the interpretive center, but the GPS label does not establish parking/entrance point semantics.
- Preferred arrival to review: Jane Hurt Yarn Interpretive Center public parking. Terrora day-use/lake access and camping are separate visitor purposes; obtain separate endpoints when needed.
- Access: gorge-floor permits are limited to 100 daily, obtained onsite after briefings, with footwear requirements and weather/water-release restrictions. Rim access does not confer gorge-floor access. Pets are prohibited on the gorge floor and specified staircase/trail areas.
- Uncertainty: the main page still displays a summer beach/construction closure, while an [October 3 adaptive kayaking event](https://explore.gastateparks.org/info/319951?c=33054659) describes the new accessible dock. Reconfirm lake/beach availability rather than treating the undated notice as an October-wide closure. Do not interpret date-only cancellation notices without month context.
- Readiness: content ready with permit notes; exact parking point and lake-access status need review.

### 4. Cloudland Canyon

- Official name: **Cloudland Canyon State Park**; Rising Fawn agrees with [DNR](https://gastateparks.org/CloudlandCanyon).
- Address: **122 Cloudland Canyon Park Road, Rising Fawn, GA 30738**.
- Proposed description: A Lookout Mountain park with wooded canyons, waterfalls, rim overlooks, and hiking and multi-use trails.
- [DNR location reference](https://explore.gastateparks.org/info/307518?c=33320387): **34.8402630, -85.4828810**. It is not specifically labeled a parking lot or gate.
- Candidate arrival: main day-use trailhead/overlook parking, subject to confirmation. The [official trail map](https://gastateparks.org/sites/default/files/parks/pdf/trailmaps/CloudlandCanyon_TrailMap.pdf) names Ascalon and Five Points trailheads and a Canyon Park Drive lot at the end of Sitton's Gulch Trail. These are distinct endpoints, not interchangeable with the main area.
- Access: DNR currently reports entrance road work with daytime flaggers and a temporary visitor center at the Group Lodge. Waterfall access is strenuous; the official map describes 600 steps one way and prohibits swimming. Caves require appropriate permitted/guided access.
- Readiness: content ready with construction notice; multiple endpoints need exact coordinates and purpose labels.

### 5. Sweetwater Creek

- Official name: **Sweetwater Creek State Park**; Lithia Springs agrees with [DNR](https://gastateparks.org/SweetwaterCreek).
- Address: **1750 Mount Vernon Road, Lithia Springs, GA 30122**.
- Proposed description: Wooded trails follow Sweetwater Creek past historic mill ruins and rapids, with reservoir recreation elsewhere in the park.
- [DNR location reference](https://explore.gastateparks.org/info/320210): **33.753783, -84.639000**; not explicitly a parking/entrance point.
- Conflicting reference: the [official reservation listing](https://gastateparks.reserveamerica.com/camping/sweetwater-creek-state-park/r/campgroundDetails.do?contractCode=GA&parkId=530195) publishes **33.75833, -84.63583**. Do not average the points or silently choose one as the entrance.
- Preferred arrival to review: interpretive-center/hiking parking, with separate reservoir/bait-shop and Jack's Hill access where needed. The [DNR trail map](https://gastateparks.org/sites/default/files/parks/pdf/trailmaps/SweetwaterCreek_TrailMap.pdf) identifies multiple parking areas and Jack's Hill, without furnishing explicit point coordinates in the extracted text.
- Access: mill interior access is restricted to guided/authorized visits; independent exterior hikes are allowed. Swimming in the reservoir is prohibited.
- Readiness: content ready; conflicting GPS references and specific day-use endpoint unresolved.

### 6. Providence Canyon

- Official name: **Providence Canyon State Park**; Lumpkin agrees with [DNR](https://gastateparks.org/ProvidenceCanyon). No rename to an older recreation-area title is proposed.
- Address: **8930 Canyon Road, Lumpkin, GA 31815**.
- Proposed description: Colorful erosion gullies and forest trails offer canyon-rim views and hikes into a landscape shaped by historic farming practices.
- [DNR location reference](https://explore.gastateparks.org/info/320095?c=33320085&genstatic=1&myfooter=new&s=320095.0.0.5): **32.064445, -84.921913**; general park GPS, not explicitly a vehicle entrance/parking point.
- Candidate arrival: visitor-center/day-use parking for canyon hikes; exact coordinate remains unconfirmed. Camping areas should not be selected automatically for a day trip.
- Access: stay behind rim fences and on trails; do not climb or carve canyon walls. The official description warns that canyon-floor trails commonly have shallow water. Dogs must be on a six-foot leash.
- Readiness: content ready; public parking coordinate unresolved.

### 7. F.D. Roosevelt

- Official name: **F.D. Roosevelt State Park**; Pine Mountain agrees with [DNR](https://gastateparks.org/FDRoosevelt).
- Address: **2970 Georgia Highway 190, Pine Mountain, GA 31822**.
- Proposed description: A forested Pine Mountain park with extensive hiking trails, small waterfalls, historic facilities, and the Dowdell's Knob overlook.
- [DNR location reference](https://explore.gastateparks.org/info/312522?c=32115277): **32.837533, -84.815616**. This is a general location reference accompanying an office event, not documented overlook parking.
- Candidate arrival depends on the itinerary: park office, a Pine Mountain Trail trailhead, or Dowdell's Knob. A single generic park point cannot represent all three. Obtain named public parking points before assigning a primary entrance.
- Access: the current DNR page lists a fire ban at Sassafras Hill and Grindstone Gap because of lack of water. This does not establish closure of the entire park.
- Readiness: content ready; day-trip arrival purpose and specific endpoint unresolved.

### 8. Skidaway Island

- Official name: **Skidaway Island State Park**; Savannah agrees with [DNR](https://gastateparks.org/SkidawayIsland).
- Address: **52 Diamond Causeway, Savannah, GA 31411**.
- Proposed description: Maritime forest and salt-marsh trails near Savannah offer coastal scenery and wildlife watching.
- [DNR location reference](https://explore.gastateparks.org/info/312323?c=33319938&mode=m): **31.9493100, -81.053710**. The event meets at Big Ferry trailhead, but its generic park GPS field is not explicitly that trailhead's point.
- Candidate arrival: public day-use/trail parking; Big Ferry trailhead may warrant its own endpoint. Official directions warn that some GPS devices miss the left turn at the first traffic light on Skidaway Island.
- Access: main DNR page reports the Avian Trail and observation tower closed and a partial campground renovation starting February 2, 2026, scheduled for one year. Do not describe the tower as available or treat campground work as a full day-use closure.
- Readiness: content ready with dated closures; exact arrival coordinate unresolved.

### 9. Crooked River

- Official name: **Crooked River State Park**; St. Marys agrees with [DNR](https://gastateparks.org/CrookedRiver).
- Address: **6222 Charlie Smith Senior Highway, St. Marys, GA 31558**.
- Proposed description: Coastal forest and salt-marsh trails beside a tidal river offer wildlife viewing and access to boating facilities.
- [DNR location reference](https://explore.gastateparks.org/info/304911?c=33319856): **30.8422056, -81.5524702**; generic park GPS, not explicitly entrance/parking.
- Candidate arrival: nature-center/day-use parking for walks; the boat ramp is a separate purpose-specific endpoint. Do not route a nature walk to the ramp without confirmation.
- Access: tidal boating and trail recreation have different requirements. The nearby Cumberland Island ferry is a separate destination, not an entrance to this park. No whole-park closure was displayed in the reviewed overview; that is not a guarantee of availability.
- Readiness: content ready; exact day-use parking coordinate unresolved.

### 10. Island Ford

- Proposed display name: **Chattahoochee River National Recreation Area - Island Ford Unit**. This expands the abbreviation and identifies the unit rather than the entire 48-mile park.
- Locality: Sandy Springs; entrance address **8800 Roberts Drive, Sandy Springs, GA 30350**, supported by [NPS basic information](https://home.nps.gov/chat/planyourvisit/basicinfo.htm).
- Proposed description: A Chattahoochee River park unit with forest trails, river views, and the Hewlett Lodge visitor center.
- [NPS unit directions](https://www.nps.gov/chat/planyourvisit/unitdirections.htm) explicitly name the Island Ford entrance and publish **33 degrees 59 minutes 40.64 seconds N, 84 degrees 20 minutes 2.16 seconds W**. Converted, this is **33.994622222..., -84.333933333...**, matching the seed **33.994622, -84.333933** to its six decimal places. This is an entrance point, not the visitor-center parking point. The directions page was last updated December 19, 2017, so route and endpoint review are still necessary.
- [NPS directions/parking details](https://www.nps.gov/chat/planyourvisit/directions.htm) publish three named parking candidates: **Hewlett Lodge Parking Lots: 33.98708, -84.325527**; **Hewlett Pond Parking Lot: 33.988788, -84.325319**; **Island Ferry Parking Lot: 33.995113, -84.332382**. These are sourced parking coordinates, still not route-tested.
- Recommended first route-test target: Hewlett Lodge parking for a visitor-center-oriented trip. This is a proposal; retain the existing primary entrance until reviewed. NPS distinguishes the entrance address from **1978 Island Ford Parkway**, the headquarters/lodge address.
- Access: [NPS hours](https://www.nps.gov/chat/planyourvisit/hours.htm) define day use as 30 minutes before sunrise through 30 minutes after sunset, with the visitor center normally 9am-5pm except Thanksgiving and December 25. NPS [announced trail reopening July 1, 2026](https://www.nps.gov/chat/learn/news/chattahoochee-river-national-recreation-area-announces-reopening-of-island-ford-trails.htm); older construction announcements should not be treated as current closures.
- Readiness: entrance provenance supported; named parking candidates ready for route testing. No `verified_at`, publication status, or routing result should be changed by this report.

## Shared access and evidence limits

Georgia's [current ParkPass page](https://gastateparks.org/ParkPass) lists $10 per vehicle and a $70 annual pass. Historical PDFs still show older fees; use current official policy for future access notes. NPS uses its own fee/pass system; Georgia ParkPass does not substitute for it.

Main pages and event listings were inspected as of the research date. Alerts often lack expiry dates, and reservation descriptions can lag current closures. Store the check date and source separately from evergreen descriptions. No park-center coordinate was calculated. The nine state-park points above are official general location references whose exact feature type remains uncertain. Map symbols, addresses, and the presence of an official website alone do not establish a routable endpoint.

## Proposed changes for review only

### Small seed/content changes

1. Keep all ten slugs and `needs_review` statuses. Propose the fuller Amicalola and Island Ford display names, the descriptions above, and destination-specific official URLs.
2. Replace generic directory evidence with individual DNR pages plus coordinate/access sources. Preserve previously reviewed sources and destination information.
3. Keep the Island Ford entrance coordinate and attach the precise NPS unit-directions evidence. Propose three additional named parking records only after endpoint review; do not silently change its primary entrance.
4. Do not add the nine general GPS references to `destination_entrances`. First obtain official numeric entrance/parking evidence, an explicit official GIS feature, or documented park-staff confirmation. Null is preferable to an invented endpoint.
5. Keep temporary closures in dated access notes, not permanent descriptions. Reconfirm Vogel, Tallulah lake access, Cloudland construction, Skidaway closures, and Amicalola's address discrepancy before publication.

### Schema proposals requiring agreement before implementation

- Retain the existing destination/entrance separation and multiple-entrance support. Define `Destination.location` as a display point, never an implicit routing endpoint.
- Add an entrance point kind (gate, parking, visitor center, trailhead), evidence/source association, evidence check date, and review notes. `verified_at` alone cannot explain what was verified or from which source. Prefer an explicit entrance-to-source relationship over a free-text URL alone.
- Record coordinate review separately from routing outcomes. An officially sourced point must remain `routing_status = 'untested'` until an actual route test.
- Add route-test history containing the exact endpoint, driving/walking profile, provider, test timestamp, snapped endpoint, outcome, and reviewer note. Coordinate changes must invalidate stale routing approval. Walking availability must be evaluated separately from driving.
- Consider dated access advisories with scope (whole park, facility, trail), source URL, check date, and optional start/end dates. This avoids treating a closed tower as a closed park.
- Before implementing any reviewed-data import, address the importer's nullable-field overwrites on unverified destinations and its existing-source skip behavior. A reviewed field should be protected independently of whether the whole destination is verified; current status-level protection is too coarse. Preserve the existing rules that reject seed `verified` statuses, successful routing, and entrance verification timestamps.

## Acceptance sequence for the next increment

Review the proposed content and data model first. Then obtain the nine missing entrance/parking points and resolve discrepancies. Test actual driving routes to named public endpoints, inspect road access and snapping, and test walking only where supported and permitted. Review dated restrictions and image rights before publication. Promotion to `verified` should be a separate reviewed service action, never a consequence of running the seed importer.
