var inFile = new File("C:/Users/timot/Documents/Proposal-Microsite/projects/active/client/jwblng-mvp/assets/stock/hero-community.jpg");
if (!inFile.exists) { throw new Error("Input file not found"); }
app.displayDialogs = DialogModes.NO;
var doc = app.open(inFile);
// Duplicate the background layer so adjustments are non-destructive in session
var layer = doc.activeLayer.duplicate();
layer.name = "Enhanced";
doc.activeLayer = layer;

// Apply practical brightening and contrast recovery
layer.adjustBrightnessContrast(22, 14);
layer.adjustLevels(8, 1.04, 246, 4, 252);
layer.adjustHueSaturation(0, 0, 6);
layer.applyUnSharpMask(55, 1.0, 0);

// Flatten and save back as JPEG quality 11
doc.flatten();
var opts = new JPEGSaveOptions();
opts.quality = 11;
opts.embedColorProfile = true;
opts.formatOptions = FormatOptions.STANDARDBASELINE;

doc.saveAs(inFile, opts, true, Extension.LOWERCASE);
doc.close(SaveOptions.DONOTSAVECHANGES);
