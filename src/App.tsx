import { useMemo, useState } from "react";
import { LayoutDashboard, ScanFace, Settings } from "lucide-react";
import { Sidebar, Topbar } from "./components/AppShell";
import { CreateAlbumModal } from "./components/CreateAlbumModal";
import { AuthScreen } from "./pages/AuthScreen";
import { Dashboard } from "./pages/Dashboard";
import { AlbumDetails } from "./pages/AlbumDetails";
import { FaceRecognition } from "./pages/FaceRecognition";
import { ClientGallery } from "./pages/ClientGallery";
import { SettingsPage } from "./pages/SettingsPage";
import type { Screen, UploadStatus } from "./types";
import { useEffect } from "react";
import "./index.css";

type Album = {
  id: string;
  album_name: string;
  event_date: string;
  total_photos: number;
  created_at: string;
};

function App() {
  const [screen, setScreen] = useState<Screen>(() => {
    const token = localStorage.getItem("token");

    if (!token) return "login";

    return "dashboard";
  });
  useEffect(() => {
    const token = localStorage.getItem("token");

    if (!token) {
      setScreen("login");
    }
  }, []);

  const [selectedAlbum, setSelectedAlbum] = useState<Album | null>(() => {
    const saved = localStorage.getItem("selectedAlbum");
    return saved ? JSON.parse(saved) : null;
  });

  const [showCreateModal, setShowCreateModal] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const [shareActive, setShareActive] = useState(true);
  const [linkGenerated, setLinkGenerated] = useState(true);
  const [downloadProgress, setDownloadProgress] = useState(0);
  const [showEmpty, setShowEmpty] = useState(false);

  const navItems = [
    {
      label: "Dashboard",
      icon: LayoutDashboard,
      target: "dashboard" as Screen,
    },
    { label: "Face Match", icon: ScanFace, target: "face" as Screen },
    { label: "Settings", icon: Settings, target: "settings" as Screen },
  ];

  const uploadRows = useMemo(
    () => [
      {
        name: "ceremony-0428.jpg",
        status: "Completed" as UploadStatus,
        progress: 100,
      },
      {
        name: "reception-0172.jpg",
        status: "Processing AI" as UploadStatus,
        progress: 68,
      },
      {
        name: "portraits-0091.jpg",
        status: "Uploading" as UploadStatus,
        progress: 38,
      },
    ],
    [],
  );

  const beginDownload = () => {
    setDownloadProgress(18);
    window.setTimeout(() => setDownloadProgress(54), 500);
    window.setTimeout(() => setDownloadProgress(100), 1100);
  };

  if (
    screen === "login" ||
    screen === "register" ||
    screen === "clientLogin" ||
    screen === "clientRegister"
  ) {
    return <AuthScreen mode={screen} error={false} setScreen={setScreen} />;
  }

  if (screen === "clientGallery") {
    return (
      <ClientGallery
        setScreen={setScreen}
        downloadProgress={downloadProgress}
        beginDownload={beginDownload}
      />
    );
  }

  return (
    <div className="min-h-screen bg-[#F8FAFC] text-slate-950">
      <div className="fixed inset-0 -z-10 overflow-hidden">
        <div className="absolute left-[18%] top-[-10%] h-72 w-72 rounded-full bg-blue-200/40 blur-3xl" />
        <div className="absolute right-[8%] top-[8%] h-80 w-80 rounded-full bg-cyan-100/70 blur-3xl" />
      </div>
      <Sidebar navItems={navItems} active={screen} setScreen={setScreen} />
      <main className="min-h-screen pl-0 lg:pl-72">
        <Topbar
          setScreen={setScreen}
          profileOpen={profileOpen}
          setProfileOpen={setProfileOpen}
        />
        <div className="mx-auto max-w-7xl px-5 gap-6 py-6 sm:px-8 lg:px-10">
          {screen === "dashboard" && (
            <Dashboard
              showEmpty={showEmpty}
              setShowEmpty={setShowEmpty}
              setShowCreateModal={setShowCreateModal}
              setScreen={setScreen}
              setSelectedAlbum={(album: Album) => {
                setSelectedAlbum(album);
                localStorage.setItem("selectedAlbum", JSON.stringify(album)); // persist
                setScreen("album");
                localStorage.setItem("screen", "album");
              }}
            />
          )}
          {screen === "album" && (
            <AlbumDetails
              album={selectedAlbum}
              uploadRows={uploadRows}
              shareActive={shareActive}
              setShareActive={setShareActive}
              linkGenerated={linkGenerated}
              setLinkGenerated={setLinkGenerated}
            />
          )}
          {screen === "face" && <FaceRecognition />}
          {screen === "settings" && <SettingsPage />}
        </div>
      </main>
      {showCreateModal && (
        <CreateAlbumModal onClose={() => setShowCreateModal(false)} />
      )}
    </div>
  );
}

export default App;
