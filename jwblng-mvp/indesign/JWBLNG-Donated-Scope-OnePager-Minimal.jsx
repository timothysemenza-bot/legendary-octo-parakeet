/*
  Minimal fallback script for InDesign.
  Purpose: create a one-page JWBLNG donated scope doc with plain text formatting only.
*/

try {
    app.scriptPreferences.userInteractionLevel = UserInteractionLevels.interactWithAll;

    var doc = app.documents.add();
    doc.documentPreferences.facingPages = false;
    doc.documentPreferences.pageWidth = "8.5in";
    doc.documentPreferences.pageHeight = "11in";

    var page = doc.pages.item(0);

    // Safe fixed bounds (points): [top, left, bottom, right]
    var tf = page.textFrames.add({
        geometricBounds: [36, 36, 756, 576]
    });

    var story = tf.parentStory;

    function line(txt) {
        story.insertionPoints[-1].contents = txt + "\r";
    }

    line("JWBLNG Donated Scope (Constrained MVP)");
    line("Date: February 24, 2026");
    line("");
    line("Purpose");
    line("Provide JWBLNG with a focused, no-cost starter implementation that creates immediate clarity and momentum without open-ended scope.");
    line("");
    line("Donated Deliverables");
    line("1. Member Journey Blueprint (1 page)");
    line("• Clear path: discover -> join -> onboard -> first event -> ongoing communications");
    line("2. Website MVP (client-facing)");
    line("• Main homepage");
    line("• 3 standalone event pages");
    line("• Member portal mock view");
    line("3. Communication Starter Pack");
    line("• Welcome email template");
    line("• Event reminder template");
    line("• Monthly digest template");
    line("• Simple monthly send calendar + owner checklist");
    line("4. Basic Launch Setup");
    line("• One canonical Join path");
    line("• One standard event registration flow");
    line("• One donation CTA path");
    line("• Basic click/form tracking tags");
    line("5. Handoff Session (60-90 min)");
    line("• Walkthrough of what is delivered");
    line("• Operating guidance for JWBLNG team");
    line("• Decision checkpoint for any later paid phase");
    line("");
    line("Timeline");
    line("• Total duration: up to 3 weeks from kickoff/alignment");
    line("• Includes one consolidated revision round");
    line("");
    line("Explicitly Out of Scope (Donated Phase)");
    line("• Full Kajabi migration or complete platform rebuild");
    line("• Custom backend/CRM development");
    line("• Advanced third-party integrations");
    line("• Ongoing content/admin management after handoff");
    line("• Unlimited revision cycles");
    line("");
    line("Assumptions");
    line("• JWBLNG provides timely content inputs and approvals");
    line("• Required platform/logins are available as needed");
    line("• Decision-makers are available for one review checkpoint and final handoff");
    line("");
    line("Success Criteria for This Phase");
    line("• A clear and usable member path");
    line("• Event pages that can be shared publicly");
    line("• Consistent communication templates the team can run");
    line("• A concrete basis for deciding whether a later paid phase is needed");

    // Light formatting only (safe defaults)
    story.paragraphs.item(0).pointSize = 20;
    story.paragraphs.item(0).leading = 24;
    story.paragraphs.item(0).fontStyle = "Bold";
    story.paragraphs.item(1).pointSize = 10;
    story.paragraphs.everyItem().appliedFont = app.fonts.item(0);

    alert("Minimal JWBLNG one-pager created successfully.");
} catch (e) {
    alert("Script failed: " + e + "\rLine: " + (e.line || "n/a"));
}
