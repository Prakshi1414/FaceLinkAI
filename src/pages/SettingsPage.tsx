import { Camera, User } from "lucide-react";
import { ErrorMessage, Input, ToggleRow } from "../components/FormPrimitives";

export function SettingsPage() {
  return (
    <div>
      <div className="mb-8">
        <p className="text-sm font-semibold uppercase tracking-[0.16em] text-blue-700">
          Settings
        </p>
        <h1 className="mt-2 text-4xl font-bold tracking-tight">
          Workspace settings
        </h1>
      </div>
      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-xl font-bold">Studio profile</h2>
          <div className="mt-5 space-y-4">
            <Input
              label="Studio name"
              icon={Camera}
              placeholder="Maya Studio"
            />
            <Input
              label="Contact phone"
              icon={User}
              placeholder="+1 (555) 014-2894"
            />
          </div>
        </div>
        <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-xl font-bold">Notifications</h2>
          <div className="mt-5 space-y-3">
            <ToggleRow title="Upload completed" active />
            <ToggleRow title="Client downloaded gallery" active />
            <ToggleRow title="Network or auth errors" active />
          </div>
          <ErrorMessage text="Network error example: unable to sync one client invite. Retrying automatically." />
        </div>
      </div>
    </div>
  );
}
