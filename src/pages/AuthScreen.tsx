import { KeyRound, Lock, Sparkles, User } from "lucide-react";
import { motion } from "framer-motion";
import { BrandMark } from "../components/BrandMark";
import { ErrorMessage, Input } from "../components/FormPrimitives";
import type { Screen } from "../types";
import { useState } from "react";

type ErrorType = {
  studioName?: string;
  username?: string;
  mobileNumber?: string;
  email?: string;
  password?: string;
};

export function AuthScreen({
  mode,
  error,
  setScreen,
}: {
  mode: Screen;
  error: boolean;
  setScreen: (screen: Screen) => void;
}) {
  const [studioName, setStudioName] = useState("");
  const [username, setUsername] = useState("");
  const [mobileNumber, setMobileNumber] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState<Record<string, string>>({});

  const [loginMobile, setLoginMobile] = useState("");
  const [loginPassword, setLoginPassword] = useState("");

  const validate = () => {
    const newErrors: ErrorType = {};

    // Studio Name
    if (!studioName || studioName.length < 2) {
      newErrors.studioName = "Enter valid studio name";
    }

    // Username
    if (!username || username.length < 3) {
      newErrors.username = "Username must be at least 3 characters";
    }

    // Mobile (10 digits only)
    if (!/^\d{10}$/.test(mobileNumber)) {
      newErrors.mobileNumber = "Enter valid 10 digit number";
    }

    // Email
    if (!/^\S+@\S+\.\S+$/.test(email)) {
      newErrors.email = "Enter valid email";
    }

    // Password (strong)
    if (!/^(?=.*[A-Z])(?=.*\d).{8,}$/.test(password)) {
      newErrors.password = "Password must be 8+ chars, 1 uppercase, 1 number";
    }

    setErrors(newErrors);

    return Object.keys(newErrors).length === 0;
  };

  const handleRegister = async () => {
    // ✅ VALIDATION CALL (MISSING THA)
    console.log("BUTTON CLICKED");
    if (!validate()) return;

    try {
      const response = await fetch(
        `${import.meta.env.VITE_BASE_API_URL}/register-user`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            studio_name: studioName,
            username: username,
            mobile_number: mobileNumber,
            email: email,
            password: password,
          }),
        },
      );
      console.log({
        studioName,
        username,
        mobileNumber,
        email,
        password,
      });
      const data = await response.json();

      if (response.ok) {
        alert("Registration Successful ✅");
        setScreen("login");
      } else {
        if (Array.isArray(data.detail)) {
          alert(data.detail.map((err: { msg: string }) => err.msg).join("\n"));
        } else {
          alert(data.detail || "Registration failed ❌");
        }
      }
    } catch (error) {
      console.error("REGISTER ERROR:", error);
    }
  };
  const handleLogin = async () => {
    try {
      const response = await fetch(
        `${import.meta.env.VITE_BASE_API_URL}/login-user`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            mobile_number: loginMobile,
            password: loginPassword,
          }),
        },
      );

      const data = await response.json();
      console.log("LOGIN RESPONSE:", data);

      // ✅ SUCCESS
      if (response.ok && data.access_token) {
        localStorage.setItem("token", data.access_token);

        alert("Login Successful ✅");
        if (response.ok && data.access_token) {
          localStorage.setItem("token", data.access_token);

          // IMPORTANT CLEANUP
          localStorage.removeItem("selectedAlbum");
          localStorage.removeItem("screen");

          alert("Login Successful ✅");
          setScreen("dashboard");
        }
        setScreen("dashboard");
      } else {
        const type = data?.detail?.type;

        if (type === "USER_NOT_FOUND") {
          alert("Login failed, please register first ❌");
        } else if (type === "INVALID_CREDENTIALS") {
          alert("Wrong username or password ❌");
        } else {
          alert("Login failed ❌");
        }
      }
    } catch (err) {
      console.error("LOGIN ERROR:", err);
      alert("Something went wrong");
    }
  };
  const isRegister = mode === "register" || mode === "clientRegister";
  const isClient = mode === "clientLogin" || mode === "clientRegister";

  return (
    <div className="min-h-screen bg-slate-50 text-slate-950">
      <div className="grid min-h-screen lg:grid-cols-[1.05fr_0.95fr]">
        <section className="relative hidden overflow-hidden bg-gradient-to-br from-[#102A68] via-[#1E3A8A] to-slate-950 p-12 text-white lg:flex lg:flex-col lg:justify-between">
          <div className="absolute -left-24 top-24 h-72 w-72 rounded-full bg-cyan-400/20 blur-3xl" />
          <div className="absolute bottom-8 right-0 h-96 w-96 rounded-full bg-indigo-400/20 blur-3xl" />
          <BrandMark light />
          <div className="relative z-10 max-w-xl">
            <div className="mb-8 inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/10 px-4 py-2 text-sm text-blue-50 backdrop-blur">
              <Sparkles className="h-4 w-4 text-cyan-200" />
              {isClient
                ? "Client Access Portal"
                : "AI-powered delivery for premium studios"}
            </div>
            <h1 className="text-5xl font-bold tracking-tight text-white">
              Face recognition, album delivery, and client access in one calm
              workspace.
            </h1>
            <p className="mt-5 text-lg leading-8 text-blue-100">
              FaceLinkAI automatically indexes faces, organizes galleries, and
              gives every client a polished path to find and download their
              photos.
            </p>
            <div className="mt-10 rounded-[28px] border border-white/15 bg-white/10 p-4 shadow-2xl backdrop-blur-xl">
              <div className="rounded-2xl bg-slate-950/30 p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-blue-100">AI scan session</p>
                    <p className="font-semibold">Avery & Noah Wedding</p>
                  </div>
                  <div className="rounded-full bg-cyan-400/20 px-3 py-1 text-sm text-cyan-100">
                    Live
                  </div>
                </div>
                <div className="mt-5 grid grid-cols-4 gap-3">
                  {Array(4)
                    .fill(
                      "https://images.unsplash.com/photo-1519741497674-611481863552?auto=format&fit=crop&w=700&q=80",
                    )
                    .map((photo, index) => (
                      <div
                        key={photo}
                        className="relative h-28 overflow-hidden rounded-xl bg-white/10"
                      >
                        <img
                          src={photo}
                          alt="AI indexed photography preview"
                          className="h-full w-full object-cover"
                        />
                        {index === 1 && (
                          <div className="absolute inset-3 rounded-lg border-2 border-cyan-300 shadow-[0_0_28px_rgba(34,211,238,.8)]" />
                        )}
                      </div>
                    ))}
                </div>
                <div className="mt-5 h-2 overflow-hidden rounded-full bg-white/10">
                  <motion.div
                    className="h-full rounded-full bg-cyan-300"
                    initial={{ width: "18%" }}
                    animate={{ width: "82%" }}
                    transition={{
                      duration: 1.8,
                      repeat: Infinity,
                      repeatType: "reverse",
                    }}
                  />
                </div>
              </div>
            </div>
          </div>
          <p className="relative z-10 text-sm text-blue-100">
            Trusted by studios delivering high-volume weddings, portraits, and
            events.
          </p>
        </section>
        <section className="flex items-center justify-center p-5 sm:p-8">
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            className="w-full max-w-md rounded-[28px] border border-slate-200 bg-white p-7 shadow-[0_24px_70px_rgba(15,23,42,.08)]"
          >
            <div className="mb-8 lg:hidden">
              <BrandMark />
            </div>
            <p className="text-sm font-semibold uppercase tracking-[0.18em] text-blue-700">
              {isClient ? "Client Access" : "Studio Workspace"}
            </p>
            <h2 className="mt-2 text-3xl font-bold tracking-tight text-slate-950">
              {isRegister ? "Create your account" : "Welcome back"}
            </h2>
            <p className="mt-2 text-sm leading-6 text-slate-500">
              {isClient
                ? "Access your private album and face-matched photos."
                : "Manage AI albums, uploads, share links, and client galleries."}
            </p>
            <div className="mt-8 space-y-4">
              {isRegister && (
                <>
                  <Input
                    label="Studio Name"
                    icon={User}
                    placeholder="Studio Name"
                    value={studioName}
                    onChange={(e) => setStudioName(e.target.value)}
                    error={errors.studioName}
                  />
                  <Input
                    label="Username"
                    icon={User}
                    placeholder="Username"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    error={errors.username}
                  />

                  <Input
                    label="Mobile Number"
                    icon={User}
                    placeholder="9876543210"
                    value={mobileNumber}
                    onChange={(e) => setMobileNumber(e.target.value)}
                    error={errors.mobileNumber}
                  />

                  <Input
                    label="Email"
                    icon={User}
                    placeholder="test@gmail.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    error={errors.email}
                  />

                  <Input
                    label="Password"
                    icon={Lock}
                    type="password"
                    placeholder="••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    error={errors.password}
                  />
                </>
              )}
              {!isRegister && (
                <>
                  <Input
                    label="Mobile Number"
                    icon={User}
                    placeholder="9876543210"
                    value={loginMobile}
                    onChange={(e) => setLoginMobile(e.target.value)}
                  />

                  <Input
                    label="Password"
                    icon={Lock}
                    type="password"
                    placeholder="••••••••"
                    value={loginPassword}
                    onChange={(e) => setLoginPassword(e.target.value)}
                  />
                </>
              )}

              {!isRegister && error && (
                <ErrorMessage text="Invalid credentials. The demo will continue in a moment so you can review the UI flow." />
              )}
              <button
                onClick={isRegister ? handleRegister : handleLogin}
                className="flex w-full items-center justify-center gap-2 rounded-xl bg-[#1E3A8A] px-4 py-3 font-semibold text-white shadow-lg shadow-blue-900/20 transition hover:bg-blue-800 focus:outline-none focus:ring-4 focus:ring-cyan-200"
              >
                {isRegister ? "Create Account" : "Login"}
                <KeyRound className="h-4 w-4" />
              </button>
              <button
                onClick={() =>
                  setScreen(
                    isRegister
                      ? isClient
                        ? "clientLogin"
                        : "login"
                      : isClient
                        ? "clientRegister"
                        : "register",
                  )
                }
                className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 font-semibold text-slate-700 transition hover:border-blue-200 hover:bg-blue-50/40"
              >
                {isRegister
                  ? "Already have an account? Login"
                  : "Create account"}
              </button>
              <button
                onClick={() => setScreen(isClient ? "login" : "clientLogin")}
                className="w-full text-sm font-medium text-slate-500 transition hover:text-blue-700"
              >
                Switch to {isClient ? "studio login" : "client access"}
              </button>
            </div>
          </motion.div>
        </section>
      </div>
    </div>
  );
}
