import { ScanFace } from "lucide-react";

export function BrandMark({ light = false }: { light?: boolean }) {
  return (
    <div className="relative z-10 flex items-center gap-3">
      <div
        className={`flex h-11 w-11 items-center justify-center rounded-2xl ${light ? "bg-white/15 text-cyan-200" : "bg-blue-900 text-white"} shadow-lg`}
      >
        <ScanFace className="h-6 w-6" />
      </div>
      <div>
        <p
          className={`text-xl font-bold tracking-tight ${light ? "text-white" : "text-slate-950"}`}
        >
          FaceLinkAI
        </p>
        <p className={`text-xs ${light ? "text-blue-100" : "text-slate-500"}`}>
          Intelligent photo delivery
        </p>
      </div>
    </div>
  );
}
