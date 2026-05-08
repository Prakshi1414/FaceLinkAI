import { useState } from "react";
import { Loader2 } from "lucide-react";
import { motion } from "framer-motion";
import { EmptyState } from "../components/FormPrimitives";

export function FaceRecognition() {
  const [hasMatch, setHasMatch] = useState(true);
  return (
    <div>
      <div className="mb-8">
        <p className="text-sm font-semibold uppercase tracking-[0.16em] text-blue-700">
          Face recognition
        </p>
        <h1 className="mt-2 text-4xl font-bold tracking-tight">
          Find My Photos
        </h1>
        <p className="mt-2 text-slate-500">
          Upload a reference portrait and FaceLinkAI will identify matches
          across the album.
        </p>
      </div>
      <div className="grid gap-6 lg:grid-cols-[420px_1fr]">
        <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="rounded-2xl border border-dashed border-blue-200 bg-blue-50/60 p-6 text-center">
            <div className="mx-auto h-44 w-44 overflow-hidden rounded-3xl shadow-lg">
              <img
                src="https://images.unsplash.com/photo-1508214751196-bcfd4ca60f91?auto=format&fit=crop&w=500&q=80"
                alt="Uploaded face preview"
                className="h-full w-full object-cover"
              />
            </div>
            <button className="mt-6 w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-700">
              Upload single image
            </button>
            <button
              onClick={() => setHasMatch(!hasMatch)}
              className="mt-3 w-full rounded-xl bg-[#1E3A8A] px-4 py-3 text-sm font-semibold text-white"
            >
              Find My Photos
            </button>
          </div>
          <div className="mt-5 rounded-2xl bg-slate-50 p-4">
            <div className="flex items-center gap-3">
              <Loader2 className="h-5 w-5 animate-spin text-cyan-500" />
              <div>
                <p className="text-sm font-semibold">AI scanning faces</p>
                <p className="text-xs text-slate-500">
                  Comparing 842 photos with 97.8% confidence
                </p>
              </div>
            </div>
            <div className="mt-4 h-2 rounded-full bg-white">
              <motion.div
                className="h-full rounded-full bg-cyan-500"
                animate={{ width: ["24%", "88%", "58%"] }}
                transition={{ duration: 2.2, repeat: Infinity }}
              />
            </div>
          </div>
        </div>
        <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="mb-5 flex items-center justify-between">
            <h2 className="text-xl font-bold">Matched photos</h2>
            <button
              onClick={() => setHasMatch(!hasMatch)}
              className="text-sm font-semibold text-blue-800"
            >
              Toggle no matches
            </button>
          </div>
          {hasMatch ? (
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
              {Array(4).fill("https://images.unsplash.com/photo-1519741497674-611481863552?auto=format&fit=crop&w=700&q=80").map((photo, index) => (
                <div
                  key={photo}
                  className="relative overflow-hidden rounded-2xl"
                >
                  <img
                    src={photo}
                    alt="Matched result"
                    className="aspect-[4/5] w-full object-cover"
                  />
                  <div className="absolute inset-4 rounded-xl border-2 border-cyan-300 shadow-[0_0_30px_rgba(34,211,238,.7)]" />
                  <span className="absolute bottom-3 left-3 rounded-full bg-white/90 px-3 py-1 text-xs font-semibold text-blue-900">
                    Match {98 - index}%
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState
              title="No matches found"
              text="Try a clearer face image with good lighting. FaceLinkAI will notify you when new matching photos are processed."
              action="Upload another image"
              onAction={() => setHasMatch(true)}
            />
          )}
        </div>
      </div>
    </div>
  );
}
