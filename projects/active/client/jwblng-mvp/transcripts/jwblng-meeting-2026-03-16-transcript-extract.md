# JWBLNG Meeting Transcript Extract
Meeting date: 2026-03-16
Received: 2026-03-17 from Jessica Rabinowitz
Raw source: `projects/active/client/jwblng-mvp/source-material/2026-03-17/JWBLNG Website Meeting_Transcript.docx`

## Why This Extract Exists
This extract pulls forward the transcript passages that most directly affect Phase 1 implementation, especially the homepage narrative, the public-vs-gated split, and the intended join flow.

## Phase 1 Takeaways
- The homepage was intended to carry the main explanatory burden before any gated action.
- The join action for non-members was described as a short homepage form rather than a separate deep signup experience.
- Program/event pages should support discovery and route people back into the same single join path.
- Benefits, testimonials, and program descriptions should stay public-facing, while approvals and certain event details can remain gated.

## Key Excerpts
### Homepage Form As The Join Gate
At roughly `12:31-13:10`, Timothy described the intended interaction on the homepage:

> You click join JWBLNG and it immediately drops you down to a very straightforward, this is how you sign up.

He then clarified the Phase 1 gate:

> That is the only thing that they can do if they are not part of JWBLNG currently.

### Front Page Needs The "What Is JWBLNG?" Story
At roughly `13:11-14:16`, Jessica and Marcy pushed for more context above the form:

> Should there be the advantages of joining somewhere? Like why join JWBLNG?

Marcy then clarified the homepage requirement:

> This first page ... has to be sort of an about ... what is JWBLNG, which is where we already have that text on Wix.

### Keep The Structure Straightforward
At roughly `13:54-14:12`, Timothy explained the page-structure goal:

> What I'm trying to avoid ... is creating like a rabbit warren of web pages where everything is buried under different links.

### Membership Benefits Stay Central
At roughly `58:48-1:00:10`, Marcy called out the Wix membership content that should survive into Kajabi:

> The membership blurb ... is probably ... really what we're giving.

She then named the benefits/components to keep visible:

> Monthly book club ... business halacha ... ask the rabbi WhatsApp group ... speaker series ... professional development.

She also identified two additions:

> The only thing we need to add is resources and a podcast.

## Implementation Notes
- Treat `/#block-1772192187104_0` as the canonical Phase 1 join target unless Kajabi regenerates the homepage block ID.
- Keep `/join` only as a compatibility bridge back to the homepage form.
- Ensure all public join CTAs route into the same homepage form instead of creating a parallel signup journey.
