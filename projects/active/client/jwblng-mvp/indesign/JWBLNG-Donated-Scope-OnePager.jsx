/*
  JWBLNG Donated Scope One-Pager
  InDesign ExtendScript (.jsx)
  Run from InDesign Scripts panel.
*/

app.scriptPreferences.userInteractionLevel = UserInteractionLevels.interactWithAll;

var doc = app.documents.add();
doc.documentPreferences.properties = {
    pageWidth: "8.5in",
    pageHeight: "11in",
    pagesPerDocument: 1,
    facingPages: false
};

var page = doc.pages.item(0);
var margins = page.marginPreferences;
margins.top = "0.65in";
margins.bottom = "0.65in";
margins.left = "0.65in";
margins.right = "0.65in";

function toPoints(v) {
    try {
        if (typeof v === "number") return v;
        return UnitValue(String(v)).as("pt");
    } catch (e) {
        return Number(v) || 0;
    }
}

var swatches = doc.swatches;
var plum;
try {
    plum = doc.colors.itemByName("JWBLNG Plum");
    plum.name;
} catch (e) {
    plum = doc.colors.add({
        name: "JWBLNG Plum",
        model: ColorModel.process,
        space: ColorSpace.CMYK,
        colorValue: [55, 90, 0, 20]
    });
}

function ensureParagraphStyle(name, props) {
    var s;
    try {
        s = doc.paragraphStyles.itemByName(name);
        s.name;
    } catch (e) {
        s = doc.paragraphStyles.add({ name: name });
    }
    for (var p in props) {
        try {
            s[p] = props[p];
        } catch (e2) {
            // Ignore unsupported font/style properties on this host.
        }
    }
    return s;
}

var pTitle = ensureParagraphStyle("JWBLNG_Title", {
    pointSize: 24,
    leading: 28,
    fillColor: plum,
    spaceAfter: 8
});

var pDate = ensureParagraphStyle("JWBLNG_Date", {
    pointSize: 10,
    leading: 13,
    fillColor: doc.swatches.itemByName("Black"),
    spaceAfter: 12
});

var pH2 = ensureParagraphStyle("JWBLNG_H2", {
    pointSize: 12,
    leading: 15,
    fillColor: plum,
    spaceBefore: 6,
    spaceAfter: 4
});

var pBody = ensureParagraphStyle("JWBLNG_Body", {
    pointSize: 10.5,
    leading: 14,
    fillColor: doc.swatches.itemByName("Black"),
    spaceAfter: 2
});

var pBullet = ensureParagraphStyle("JWBLNG_Bullet", {
    pointSize: 10.5,
    leading: 14,
    fillColor: doc.swatches.itemByName("Black"),
    leftIndent: "0.16in",
    firstLineIndent: "-0.12in",
    spaceAfter: 1
});

var tf = page.textFrames.add({
    geometricBounds: (function () {
        var pb = page.bounds; // [y1, x1, y2, x2] in points
        var top = pb[0] + toPoints(margins.top);
        var left = pb[1] + toPoints(margins.left);
        var bottom = pb[2] - toPoints(margins.bottom);
        var right = pb[3] - toPoints(margins.right);
        return [top, left, bottom, right];
    })()
});

function addLine(text, style) {
    tf.parentStory.insertionPoints[-1].contents = text + "\r";
    tf.parentStory.paragraphs[-1].appliedParagraphStyle = style;
}

function addBullets(items) {
    for (var i = 0; i < items.length; i++) {
        addLine("• " + items[i], pBullet);
    }
}

addLine("JWBLNG Donated Scope (Constrained MVP)", pTitle);
addLine("Date: February 24, 2026", pDate);

addLine("Purpose", pH2);
addLine("Provide JWBLNG with a focused, no-cost starter implementation that creates immediate clarity and momentum without open-ended scope.", pBody);

addLine("Donated Deliverables", pH2);
addLine("1. Member Journey Blueprint (1 page)", pBody);
addBullets(["Clear path: discover -> join -> onboard -> first event -> ongoing communications"]);
addLine("2. Website MVP (client-facing)", pBody);
addBullets(["Main homepage", "3 standalone event pages", "Member portal mock view"]);
addLine("3. Communication Starter Pack", pBody);
addBullets(["Welcome email template", "Event reminder template", "Monthly digest template", "Simple monthly send calendar + owner checklist"]);
addLine("4. Basic Launch Setup", pBody);
addBullets(["One canonical Join path", "One standard event registration flow", "One donation CTA path", "Basic click/form tracking tags"]);
addLine("5. Handoff Session (60-90 min)", pBody);
addBullets(["Walkthrough of what is delivered", "Operating guidance for JWBLNG team", "Decision checkpoint for any later paid phase"]);

addLine("Timeline", pH2);
addBullets(["Total duration: up to 3 weeks from kickoff/alignment", "Includes one consolidated revision round"]);

addLine("Explicitly Out of Scope (Donated Phase)", pH2);
addBullets(["Full Kajabi migration or complete platform rebuild", "Custom backend/CRM development", "Advanced third-party integrations", "Ongoing content/admin management after handoff", "Unlimited revision cycles"]);

addLine("Assumptions", pH2);
addBullets(["JWBLNG provides timely content inputs and approvals", "Required platform/logins are available as needed", "Decision-makers are available for one review checkpoint and final handoff"]);

addLine("Success Criteria for This Phase", pH2);
addBullets(["A clear and usable member path", "Event pages that can be shared publicly", "Consistent communication templates the team can run", "A concrete basis for deciding whether a later paid phase is needed"]);

addLine("Optional Next Phase (Only If Needed)", pH2);
addLine("If additional implementation is desired after this donated phase, a separate paid scope can be proposed with fixed deliverables, timeline, and cost.", pBody);

alert("JWBLNG one-pager created. Review and export PDF from InDesign.");
