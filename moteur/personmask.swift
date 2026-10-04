// Détourage de personne avec Vision (Apple) : lit des PNG/JPG, écrit un masque PNG (blanc = personne).
// Usage : personmask <dossier_entree> <dossier_sortie> [quality: accurate|balanced|fast]
import Foundation
import Vision
import CoreImage
import AppKit

let args = CommandLine.arguments
guard args.count >= 3 else { print("usage: personmask in_dir out_dir [accurate|balanced|fast]"); exit(1) }
let inDir = args[1], outDir = args[2]
let quality = args.count > 3 ? args[3] : "accurate"
try? FileManager.default.createDirectory(atPath: outDir, withIntermediateDirectories: true)
let files = (try? FileManager.default.contentsOfDirectory(atPath: inDir))?.filter { $0.hasSuffix(".png") || $0.hasSuffix(".jpg") }.sorted() ?? []
let ctx = CIContext()
let req = VNGeneratePersonSegmentationRequest()
req.qualityLevel = quality == "fast" ? .fast : (quality == "balanced" ? .balanced : .accurate)
req.outputPixelFormat = kCVPixelFormatType_OneComponent8
var n = 0
for f in files {
    let url = URL(fileURLWithPath: inDir).appendingPathComponent(f)
    guard let img = CIImage(contentsOf: url) else { continue }
    let handler = VNImageRequestHandler(ciImage: img, options: [:])
    do { try handler.perform([req]) } catch { print("erreur \(f): \(error)"); continue }
    guard let obs = req.results?.first as? VNPixelBufferObservation else { continue }
    var mask = CIImage(cvPixelBuffer: obs.pixelBuffer)
    let sx = img.extent.width / mask.extent.width, sy = img.extent.height / mask.extent.height
    mask = mask.transformed(by: CGAffineTransform(scaleX: sx, y: sy))
    let out = URL(fileURLWithPath: outDir).appendingPathComponent((f as NSString).deletingPathExtension + ".png")
    try? ctx.writePNGRepresentation(of: mask, to: out, format: .L8, colorSpace: CGColorSpaceCreateDeviceGray(), options: [:])
    n += 1
    if n % 50 == 0 { print("\(n)/\(files.count)"); fflush(stdout) }
}
print("OK \(n) masques")
