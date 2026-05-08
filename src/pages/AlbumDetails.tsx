import React from "react";
import {
  Check,
  Copy,
  Image as ImageIcon,
  Link,
  Loader2,
  ShieldCheck,
  Upload,
  copy,
} from "lucide-react";
import type { UploadStatus } from "../types";
import { generateShareLink, toggleShareStatus } from "../api/share";
import { useState, useEffect, useCallback, useRef, useMemo } from "react";

type UploadRowLocal = {
  name: string;
  status: UploadStatus;
  progress: number;
  message?: string | null;
  personId?: string;
  preview?: string;
  photo?: string | null;
};

type UploadResultItem = {
  filename: string;
  status: "ok" | "error";
  person_id: string;
  message: string | null;
  img_path?: string;
  url?: string;
  path?: string;
};

type UploadResponse = {
  results: UploadResultItem[];
};

type Album = {
  id: string;
  album_name: string;
  event_date: string;
  total_photos: number;
  created_at: string;
};

export function AlbumDetails({
  album,
  shareActive,
  setShareActive,
  linkGenerated,
  setLinkGenerated,
}: {
  album: Album | null;
  uploadRows: { name: string; status: UploadStatus; progress: number }[];
  shareActive: boolean;
  setShareActive: (active: boolean) => void;
  linkGenerated: boolean;
  setLinkGenerated: (generated: boolean) => void;
}) {
  // STATE
  const [files, setFiles] = useState<File[]>([]);
  const [photos, setPhotos] = useState<UploadRowLocal[]>([]);
  const [shareLink, setShareLink] = useState("");
  const [loading, setLoading] = useState(true);
  const [uploadRowsLocal, setUploadRowsLocal] = useState<UploadRowLocal[]>([]);
  const isFetchingRef = useRef(false);
  const albumId = useMemo(() => album?.id, [album?.id]);

  // Memoize photo elements to prevent unnecessary re-renders
  const photoElements = useMemo(() => {
    return photos.map((row, index) => (
      <PhotoCard
        key={`${row.personId || "no-id"}-${row.name}-${index}`}
        photo={row.photo || "assets/placeholder.jpg"}
        processed={true}
      />
    ));
  }, [photos]);

  const fetchAlbumPhotos = useCallback(
    async (specificAlbumId?: string) => {
      const targetId = specificAlbumId || albumId;
      if (!targetId || isFetchingRef.current) return;

      isFetchingRef.current = true;
      setLoading(true);

      try {
        const token = localStorage.getItem("token");
        console.log("Fetching photos for album:", targetId);

        const res = await fetch(
          `${import.meta.env.VITE_BASE_API_URL}/album/${targetId}`,
          {
            method: "GET",
            headers: {
              Authorization: `Bearer ${token}`,
              "Content-Type": "application/json",
            },
          },
        );

        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.message || `Error ${res.status}`);
        }

        const data = await res.json();

        const mapped = (data.photos || []).map((item: any) => ({
          name: item.filename,
          status: "Completed",
          progress: 100,
          photo: item.img_path
            ? `${import.meta.env.VITE_BASE_IMAGES_URL}/${item.img_path.replace(/\\/g, "/")}`
            : "assets/placeholder.jpg",
          personId: item.person_id,
        }));

        setPhotos(mapped);
      } catch (err) {
        console.error("Failed to fetch photos:", err);
        setPhotos([]);
      } finally {
        setLoading(false);
        isFetchingRef.current = false;
      }
    },
    [albumId], // ← Changed from album?.id
  );
  useEffect(() => {
    if (albumId) {
      fetchAlbumPhotos();
    }
  }, [albumId]);

  // ✅ UPLOAD API
  const handleUpload = async () => {
    if (!files.length) return;

    const token = localStorage.getItem("token");

    const formData = new FormData();

    formData.append("album_id", album?.id || ""); // IMPORTANT FIX

    files.forEach((file) => {
      formData.append("files", file);
    });

    // initial UI state
    setUploadRowsLocal(
      files.map((f) => ({
        name: f.name,
        status: "Uploading",
        progress: 30,
        message: null,
      })),
    );

    try {
      const res = await fetch(
        `${import.meta.env.VITE_BASE_API_URL}/upload-album-photos`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
          },
          body: formData,
        },
      );

      const data = await res.json();

      const typedData = data as UploadResponse;

      const mapped: UploadRowLocal[] = typedData.results.map((item, index) => {
        return {
          name: item.filename,
          status: item.status === "ok" ? "Completed" : "Failed",
          progress: 100,
          message: item.message,
          preview: uploadRowsLocal[index]?.preview,
          personId: item.person_id,

          photo:
            item.url ||
            (item.img_path
              ? `${import.meta.env.VITE_BASE_IMAGES_URL}/${item.img_path}`
              : item.path
                ? `${import.meta.env.VITE_BASE_IMAGES_URL}/${item.path}`
                : null),
        };
      });

      setPhotos(mapped);
    } catch (err) {
      console.error(err);
    }
    await fetchAlbumPhotos(album?.id); // ✅ THIS IS THE REAL FIX

    setTimeout(() => {
      setUploadRowsLocal([]);
    }, 300);
  };

  const handleShareClick = async () => {
    try {
      console.log("Share button clicked");

      if (!albumId) {
        console.log("No album ID");
        return;
      }

      setLoading(true);

      const data = await generateShareLink(albumId); // ✅ FIX HERE

      console.log("Share API response:", data);

      const fullUrl = `${import.meta.env.VITE_BASE_API_URL}/album/share/${data.share_link}`;

      setShareLink(fullUrl);

      navigator.clipboard.writeText(fullUrl);
    } catch (err) {
      console.error("Share link error:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="mb-8 flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.16em] text-blue-700">
            Album details
          </p>
          <h1 className="mt-2 text-4xl font-bold tracking-tight">
            {album?.album_name}
          </h1>
          <p className="mt-2 text-slate-500">
            {album?.total_photos} photos • Created{" "}
            {album?.created_at
              ? new Date(album.created_at).toDateString()
              : "No date"}
          </p>
        </div>
        <button
          onClick={handleShareClick}
          className="flex items-center justify-center gap-2 rounded-xl bg-[#1E3A8A] px-5 py-3 text-sm font-semibold text-white shadow-lg shadow-blue-900/20"
        >
          <Link className="h-4 w-4" />
          {loading ? "Loading..." : "Share"}
        </button>

        {shareLink && (
          <div className="mt-3 flex items-center justify-between rounded-xl bg-slate-100 px-3 py-2 text-sm">
            {/* LINK TEXT */}
            <span className="truncate">{shareLink}</span>

            {/* COPY ICON */}
            <button
              onClick={() => {
                navigator.clipboard.writeText(shareLink);
              }}
              className="ml-2 rounded bg-white p-1 shadow hover:bg-gray-100"
            >
              <Copy className="h-4 w-4 text-gray-700" />
            </button>
          </div>
        )}
      </div>

      <div className="grid gap-6 xl:grid-cols-[1fr_360px]">
        <div className="space-y-6">
          <div className="rounded-3xl border border-dashed border-blue-200 bg-white p-8 shadow-sm">
            <div className="flex flex-col items-center justify-center rounded-2xl bg-gradient-to-br from-blue-50 to-cyan-50 px-6 py-12 text-center">
              <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-white text-blue-800 shadow-sm">
                <Upload className="h-8 w-8" />
              </div>

              <h2 className="mt-5 text-2xl font-bold">
                Drag & drop images here
              </h2>

              <p className="mt-2 max-w-md text-slate-500">
                Upload JPEG, PNG, or JPG. FaceLinkAI will process uploads
                automatically.
              </p>

              <label className="mt-6 inline-block cursor-pointer rounded-xl bg-[#1E3A8A] px-5 py-3 text-sm font-semibold text-white shadow-lg shadow-blue-900/20">
                Upload images
                <input
                  type="file"
                  multiple
                  className="hidden"
                  onChange={(e) => {
                    const selectedFiles = Array.from(e.target.files || []);
                    setFiles(selectedFiles);

                    const newRows = selectedFiles.map(
                      (file): UploadRowLocal => ({
                        name: file.name,
                        status: "Uploading",
                        progress: 0,
                        preview: URL.createObjectURL(file),
                      }),
                    );
                    setUploadRowsLocal(newRows);
                  }}
                />
              </label>

              {/* FIXED: upload trigger button */}
              <button
                onClick={handleUpload}
                className="mt-4 rounded-xl bg-green-600 px-5 py-2 text-sm font-semibold text-white"
              >
                Start Upload
              </button>
            </div>
          </div>

          <UploadProgress rows={uploadRowsLocal} />

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {loading ? (
              <p>Loading photos...</p>
            ) : photos.length > 0 ? (
              photoElements
            ) : (
              <p>No images found</p>
            )}
          </div>
        </div>

        <SharePanel
          albumId={album?.id || ""}
          shareActive={shareActive}
          setShareActive={setShareActive}
          linkGenerated={linkGenerated}
          setLinkGenerated={setLinkGenerated}
        />
      </div>
    </div>
  );
}

/* ================= UPLOAD PROGRESS ================= */

function UploadProgress({
  rows,
}: {
  rows: { name: string; status: UploadStatus; progress: number }[];
}) {
  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="mb-5 flex items-center justify-between">
        <h3 className="text-lg font-bold">Upload progress</h3>
      </div>

      <div className="space-y-4">
        {rows.map((row, i) => (
          <div
            key={`${row.name}-${i}`}
            className="rounded-2xl border border-slate-100 bg-slate-50 p-4"
          >
            <div className="mb-3 flex items-center justify-between gap-3">
              <div className="flex items-center gap-3">
                <div className="rounded-xl bg-white p-2 text-blue-800 shadow-sm">
                  <ImageIcon className="h-4 w-4" />
                </div>

                <div>
                  <p className="text-sm font-semibold text-slate-800">
                    {row.name}
                  </p>
                  <p className="text-xs text-slate-500">{row.status}</p>
                </div>
              </div>

              {row.status === "Completed" ? (
                <Check className="h-5 w-5 text-green-500" />
              ) : (
                <Loader2 className="h-5 w-5 animate-spin text-cyan-500" />
              )}
            </div>

            <div className="h-2 rounded-full bg-white">
              <div
                className={`h-full rounded-full ${
                  row.status === "Completed" ? "bg-green-500" : "bg-cyan-500"
                }`}
                style={{ width: `${row.progress}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ================= PHOTO CARD ================= */

const PhotoCard = React.memo(
  ({ photo, processed }: { photo: string; processed: boolean }) => {
    return (
      <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        <div className="relative aspect-[4/5] overflow-hidden">
          <img
            src={photo || "src/assets/placeholder.jpg"}
            onError={(e) => {
              const target = e.currentTarget as HTMLImageElement;
              if (target.src !== "src/assets/placeholder.jpg") {
                target.src = "src/assets/placeholder.jpg";
              }
            }}
            className="h-full w-full object-cover"
            loading="lazy" // ← Add this
          />
          <span
            className={`absolute left-3 top-3 rounded-full px-2.5 py-1 text-xs font-semibold ${
              processed
                ? "bg-green-50 text-green-700"
                : "bg-amber-50 text-amber-700"
            }`}
          >
            {processed ? "Processed" : "Processing"}
          </span>
        </div>
      </div>
    );
  },
);
/* ================= SHARE PANEL ================= */
function SharePanel({
  albumId,
  shareActive,
  setShareActive,
  linkGenerated,
  setLinkGenerated,
}: {
  albumId: string;
  shareActive: boolean;
  setShareActive: (active: boolean) => void;
  linkGenerated: boolean;
  setLinkGenerated: (generated: boolean) => void;
}) {
  const [shareLink, setShareLink] = useState("");
  const [loading, setLoading] = useState(false);

  const handleGenerateLink = async () => {
    try {
      setLoading(true);

      const data = await generateShareLink(albumId);

      setShareLink(data.share_link);
      setLinkGenerated(true);
    } catch (err) {
      console.error("Generate link error:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleToggleShare = async () => {
    try {
      const newStatus = !shareActive;

      setShareActive(newStatus); // optimistic UI

      await toggleShareStatus(albumId, newStatus);
    } catch (err) {
      console.error("Toggle error:", err);
    }
  };

  return (
    <aside className="h-fit rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-bold">Share link</h3>
        <ShieldCheck className="h-5 w-5 text-green-500" />
      </div>

      <p className="mt-2 text-sm text-slate-500">
        Secure client sharing system.
      </p>

      <button
        onClick={handleGenerateLink}
        className="mt-5 w-full rounded-xl bg-[#1E3A8A] px-4 py-3 text-sm font-semibold text-white"
      >
        {loading ? "Generating..." : "Generate link"}
      </button>

      <div className="mt-5 flex items-center justify-between rounded-2xl border border-slate-200 p-4">
        <div>
          <p className="text-sm font-semibold">Link status</p>
          <p className="text-xs text-slate-500">
            {shareActive ? "Active" : "Inactive"}
          </p>
        </div>

        <button
          onClick={handleToggleShare}
          className={`flex h-7 w-12 items-center rounded-full p-1 transition ${
            shareActive ? "bg-cyan-500" : "bg-slate-200"
          }`}
        >
          <span
            className={`h-5 w-5 rounded-full bg-white shadow transition ${
              shareActive ? "translate-x-5" : ""
            }`}
          />
        </button>
      </div>

      {linkGenerated && (
        <div className="mt-5 rounded-2xl bg-slate-50 p-3 text-sm">
          {shareLink}
        </div>
      )}
    </aside>
  );
}
