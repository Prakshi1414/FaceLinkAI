export const generateShareLink = async (albumId: string) => {
  const token = localStorage.getItem("token");
  const res = await fetch(
    `${import.meta.env.VITE_BASE_API_URL}/album/generate-share-link`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        album_id: albumId, // MUST be UUID string
      }),
    },
  );

  if (!res.ok) {
    throw new Error("Failed to generate share link");
  }

  return await res.json();
};

export const toggleShareStatus = async (albumId: string, active: boolean) => {
  const token = localStorage.getItem("token");

  const res = await fetch(
    `${import.meta.env.VITE_BASE_API_URL}/album/toggle-share`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        album_id: albumId,
        is_active: active,
      }),
    },
  );

  if (!res.ok) {
    throw new Error("Toggle failed");
  }

  return await res.json();
};


export const getShareLink = async (share_link: string) => {
  const token = localStorage.getItem("token");

  const res = await fetch(
    `${import.meta.env.VITE_BASE_API_URL}/album/share/${share_link}`,
    {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    },
  );

  if (!res.ok) {
    throw new Error("Failed to fetch shared album");
  }

  return await res.json();
};
