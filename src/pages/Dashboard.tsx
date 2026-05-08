import { Images, Plus, ScanFace, ShieldCheck } from "lucide-react";
import { EmptyState } from "../components/FormPrimitives";
import type { IconType, Screen } from "../types";
import { useEffect, useState } from "react";

// Album type (adjust if your backend differs)
type Album = {
  id: string;
  album_name: string;
  event_date: string;
  total_size: number;
  is_active: boolean;
  total_photos: number;
  created_at: string;
  share_link: string | null;
};

export function Dashboard({
  showEmpty,
  setShowEmpty,
  setShowCreateModal,
  setScreen,
  setSelectedAlbum,
}: {
  showEmpty: boolean;
  setShowEmpty: (empty: boolean) => void;
  setShowCreateModal: (show: boolean) => void;
  setScreen: (screen: Screen) => void;
  setSelectedAlbum: (album: Album) => void;
}) {
  const [albums, setAlbums] = useState<Album[]>([]);
  const totalAlbums = albums.length;

  const totalSize = albums.reduce((acc, album) => {
    return acc + Number(album.total_size || 0);
  }, 0);

  const activeLinks = albums.filter(
    (album) => album.is_active === true || album.share_link,
  ).length;

  useEffect(() => {
    const fetchAlbums = async () => {
      try {
        const token = localStorage.getItem("token");

        const res = await fetch(`${import.meta.env.VITE_BASE_API_URL}/get-albums`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        const data = await res.json();
        console.log("RAW ALBUM RESPONSE:", data);

        // ✅ FIX: normalize backend response
        const normalized = Array.isArray(data)
          ? data
          : Array.isArray(data?.albums)
            ? data.albums
            : data?.data || [];

        setAlbums(normalized);
      } catch (err) {
        console.error(err);
        setAlbums([]);
      }
    };

    fetchAlbums();
    // 🔥 auto refresh when new album created
    window.addEventListener("albumCreated", fetchAlbums);

    return () => window.removeEventListener("albumCreated", fetchAlbums);
  }, []);
  console.log("ALBUMS STATE:", albums);
  return (
    <div>
      {/* HEADER */}
      <div className="mb-8 flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.16em] text-blue-700">
            Dashboard
          </p>
          <h1 className="mt-2 text-4xl font-bold tracking-tight text-slate-950">
            Your Albums
          </h1>
          <p className="mt-2 text-slate-500">
            Create, process, and securely deliver AI-powered galleries.
          </p>
        </div>

        <div className="flex gap-3">
          <button
            onClick={() => setShowEmpty(!showEmpty)}
            className="rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-700 shadow-sm hover:bg-slate-50"
          >
            {showEmpty ? "Show albums" : "Preview empty state"}
          </button>

          <button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center gap-2 rounded-xl bg-[#1E3A8A] px-5 py-3 text-sm font-semibold text-white shadow-lg shadow-blue-900/20 hover:bg-blue-800"
          >
            <Plus className="h-4 w-4" /> Create Album
          </button>
        </div>
      </div>

      {/* METRICS */}
      <div className="mb-8 grid gap-4 md:grid-cols-3">
        <MetricCard
          icon={Images}
          label="Total albums"
          value={totalAlbums.toString()}
          trend="Live data"
        />

        <MetricCard
          icon={ScanFace}
          label="Total storage"
          value={`${(totalSize / (1024 * 1024)).toFixed(2)} MB`}
          trend="From backend"
        />

        <MetricCard
          icon={ShieldCheck}
          label="Active share links"
          value={activeLinks.toString()}
          trend="From albums"
        />
      </div>

      {showEmpty || (albums || []).length === 0 ? (
        <EmptyState
          title="No albums yet"
          text="Create your first album to begin uploading and processing photos."
          action="Create Album"
          onAction={() => setShowCreateModal(true)}
        />
      ) : (
        <div className="grid gap-6 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4">
          {(albums || []).map((album) => (
            <AlbumCard
              key={album.id}
              album={album}
              onOpen={() => {
                localStorage.setItem("selectedAlbum", JSON.stringify(album)); // ✅ ADD
                setSelectedAlbum(album);
                setScreen("album");
              }}
            />
          ))}
        </div>
      )}
    </div>
  );
}

//METRIC CARD
function MetricCard({
  icon: Icon,
  label,
  value,
  trend,
}: {
  icon: IconType;
  label: string;
  value: string;
  trend: string;
}) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-center justify-between">
        <div className="rounded-xl bg-blue-50 p-2.5 text-blue-800">
          <Icon className="h-5 w-5" />
        </div>
        <span className="rounded-full bg-green-50 px-2.5 py-1 text-xs font-semibold text-green-700">
          Live
        </span>
      </div>

      <p className="mt-5 text-sm text-slate-500">{label}</p>
      <p className="mt-1 text-3xl font-bold text-slate-950">{value}</p>
      <p className="mt-2 text-sm text-slate-500">{trend}</p>
    </div>
  );
}

function AlbumCard({ album, onOpen }: { album: Album; onOpen: () => void }) {
  return (
    <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm transition hover:-translate-y-1 hover:shadow-xl">
      {/* CARD CONTENT (NO GLOBAL CLICK) */}
      <div className="p-5">
        {/* ALBUM NAME */}
        <h3 className="text-lg font-bold text-slate-950">
          {album.album_name || "Untitled Album"}
        </h3>

        {/* DATE */}
        <div className="mt-2 text-sm text-slate-500">
          {album.event_date || "No date"}
        </div>

        {/* UPLOAD BUTTON */}
        <button
          onClick={onOpen}
          className="mt-4 w-full rounded-xl bg-[#1E3A8A] px-4 py-2 text-sm font-semibold text-white hover:bg-blue-800"
        >
          Upload Images
        </button>
      </div>
    </div>
  );
}
