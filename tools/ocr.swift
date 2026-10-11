// Apple Vision OCR: prints one JSON line per image with every recognised text line and its box.
// usage: ocr <lang,lang> <cropLeftFraction> <img>...   (box: x,y,w,h in pixels of the cropped image, origin top-left)
import Foundation
import Vision
import AppKit

let args = CommandLine.arguments
let langs = args[1].split(separator: ",").map(String.init)
let frac = Double(args[2]) ?? 1.0
for path in args.dropFirst(3) {
    guard let img = NSImage(contentsOfFile: path),
          var cg = img.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
        print("{\"file\":\"\(path)\",\"error\":\"load\"}"); continue
    }
    if frac < 1.0, let c = cg.cropping(to: CGRect(x: 0, y: 0, width: Int(Double(cg.width) * frac), height: cg.height)) { cg = c }
    let req = VNRecognizeTextRequest()
    req.recognitionLevel = .accurate
    req.recognitionLanguages = langs
    req.usesLanguageCorrection = false
    let h = VNImageRequestHandler(cgImage: cg, options: [:])
    try? h.perform([req])
    var lines: [[String: Any]] = []
    for o in req.results ?? [] {
        guard let t = o.topCandidates(1).first else { continue }
        let b = o.boundingBox
        lines.append(["t": t.string, "c": t.confidence,
                      "b": [Int(b.minX * Double(cg.width)), Int((1 - b.maxY) * Double(cg.height)),
                            Int(b.width * Double(cg.width)), Int(b.height * Double(cg.height))]])
    }
    let obj: [String: Any] = ["file": path, "w": cg.width, "h": cg.height, "lines": lines]
    let data = try! JSONSerialization.data(withJSONObject: obj)
    print(String(data: data, encoding: .utf8)!)
    fflush(stdout)
}
