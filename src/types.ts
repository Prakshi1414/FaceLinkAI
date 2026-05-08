import type { LucideIcon } from 'lucide-react'

export type Screen = 'login' | 'register' | 'dashboard' | 'album' | 'clientLogin' | 'clientRegister' | 'clientGallery' | 'face' | 'settings'
export type UploadStatus =
  | "Uploading"
  | "Processing AI"
  | "Completed"
  | "Failed";
export type IconType = LucideIcon
