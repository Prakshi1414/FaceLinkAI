import { FolderPlus, X, Calendar } from "lucide-react";
import { motion } from "framer-motion";
import { Input } from "./FormPrimitives";
import { useState } from "react";

export function CreateAlbumModal({ onClose }: { onClose: () => void }) {
  const [albumName, setAlbumName] = useState(""); // ✅ ADD
  const [eventDate, setEventDate] = useState(""); // ✅ ADD

  const handleCreate = async () => {
    try {
      const token = localStorage.getItem("token");

      const res = await fetch(`${import.meta.env.VITE_BASE_API_URL}/create-album`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          album_name: albumName,
          event_date: eventDate,
        }),
      });

      const data = await res.json();
      console.log("CREATE:", data);

      if (res.ok) {
        alert("Album created successfully!");
        onClose();

        window.dispatchEvent(new Event("albumCreated"));
      } else {
        alert(data?.detail?.message || "Failed");
      }
    } catch (err) {
      console.error(err);
    }
  };
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/40 p-5 backdrop-blur-md">
      <motion.div
        initial={{ opacity: 0, scale: 0.96, y: 10 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        className="w-full max-w-lg rounded-3xl border border-slate-200 bg-white p-6 shadow-2xl"
      >
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold">Create Album</h2>
            <p className="mt-1 text-sm text-slate-500">
              Start a new AI-ready client gallery.
            </p>
          </div>
          <button
            onClick={onClose}
            className="rounded-xl p-2 text-slate-500 hover:bg-slate-50"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
        <div className="space-y-4">
          <Input
            label="Album name"
            icon={FolderPlus}
            placeholder="Spring Editorial Session"
            value={albumName}
            onChange={(e) => setAlbumName(e.target.value)}
          />
          <Input
            label="Event Date"
            icon={Calendar} // ya koi bhi icon (Calendar better hai)
            placeholder="Select event date"
            type="date"
            value={eventDate}
            onChange={(e) => setEventDate(e.target.value)}
          />
          <label className="block">
            <span className="mb-2 block text-sm font-semibold text-slate-700">
              Description{" "}
              <span className="font-normal text-slate-400">(optional)</span>
            </span>
            <textarea
              className="min-h-28 w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none transition placeholder:text-slate-400 focus:border-cyan-400 focus:ring-4 focus:ring-cyan-100"
              placeholder="Private notes for the studio team..."
            />
          </label>
        </div>
        <div className="mt-7 flex justify-end gap-3">
          <button
            onClick={onClose}
            className="rounded-xl border border-slate-200 px-5 py-3 text-sm font-semibold text-slate-700 hover:bg-slate-50"
          >
            Cancel
          </button>
          <button
            onClick={handleCreate}
            className="rounded-xl bg-[#1E3A8A] px-5 py-3 text-sm font-semibold text-white shadow-lg shadow-blue-900/20"
          >
            Create
          </button>
        </div>
      </motion.div>
    </div>
  );
}
