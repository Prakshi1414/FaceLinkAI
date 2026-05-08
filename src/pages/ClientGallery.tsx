import { Archive, Download, FileArchive, ScanFace } from "lucide-react";
import type { Screen } from "../types";

export function ClientGallery({
  setScreen,
  downloadProgress,
  beginDownload,
}: {
  setScreen: (screen: Screen) => void;
  downloadProgress: number;
  beginDownload: () => void;
}) {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-950">
      <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/85 backdrop-blur">
        <div className="mx-auto flex h-20 max-w-7xl items-center justify-between px-5 sm:px-8">
          <div>
            <p className="text-sm text-slate-500">Client Gallery</p>
            <h1 className="text-xl font-bold">Avery & Noah Wedding</h1>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={beginDownload}
              className="flex items-center gap-2 rounded-xl bg-[#1E3A8A] px-4 py-3 text-sm font-semibold text-white"
            >
              <FileArchive className="h-4 w-4" /> Download All
            </button>
            <button
              onClick={() => setScreen("clientLogin")}
              className="rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-700"
            >
              Logout
            </button>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-5 py-8 sm:px-8">
        {downloadProgress > 0 && (
          <div className="mb-6 rounded-2xl border border-blue-100 bg-white p-4 shadow-sm">
            <div className="mb-3 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Archive className="h-5 w-5 text-blue-800" />
                <p className="font-semibold">Preparing ZIP download</p>
              </div>
              <span className="text-sm text-slate-500">
                {downloadProgress === 100
                  ? "Ready to save"
                  : `${downloadProgress}%`}
              </span>
            </div>
            <div className="h-2 rounded-full bg-slate-100">
              <div
                className="h-full rounded-full bg-cyan-500 transition-all"
                style={{ width: `${downloadProgress}%` }}
              />
            </div>
            {downloadProgress === 100 && (
              <p className="mt-3 text-sm font-medium text-green-700">
                Your archive is ready. Download will begin automatically.
              </p>
            )}
          </div>
        )}
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          <div className="rounded-3xl border border-dashed border-slate-200 bg-white p-6">
            <ScanFace className="h-8 w-8 text-blue-800" />
            <h2 className="mt-4 text-xl font-bold">Find yourself faster</h2>
            <p className="mt-2 text-sm text-slate-500">
              Use client face recognition to filter images that include you.
            </p>
            <button
              onClick={() => setScreen("face")}
              className="mt-5 rounded-xl border border-slate-200 px-4 py-2 text-sm font-semibold"
            >
              Open face search
            </button>
          </div>
          {Array(4).fill("https://images.unsplash.com/photo-1519741497674-611481863552?auto=format&fit=crop&w=700&q=80").map((photo, index) => (
            <div
              key={photo}
              className="group overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm"
            >
              <img
                src={photo}
                alt="Client gallery image"
                className="aspect-[4/3] w-full object-cover transition group-hover:scale-105"
              />
              <div className="flex items-center justify-between p-4">
                <p className="text-sm font-semibold">
                  Selected-{String(index + 1).padStart(3, "0")}.jpg
                </p>
                <button className="rounded-lg p-2 text-blue-800 hover:bg-blue-50">
                  <Download className="h-4 w-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}
