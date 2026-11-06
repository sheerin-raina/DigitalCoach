/**
 * Collection of functions for Firebase Storage.
 */
import {
  ref, 
  uploadBytes,
  getDownloadURL,
  StorageReference,
} from "firebase/storage";
import { v4 as uuidv4 } from "uuid"; 
import { auth } from "@App/lib/firebase/firebase.config";
import { storage } from "@App/lib/firebase/firebase.config"; // import firebase storage service from firebase configuration

export enum EStorageFolders {
  profilePic = "profilePic",
  videos = "videos",
}

/**
 * Uploads a given file to a specific folder in Firebase Storage and returns the download URL.
 */
export async function uploadFile(file: File, folder: EStorageFolders, filename: string = uuidv4()) {
  const uid = auth.currentUser?.uid;
  if (!uid) throw new Error("Authentication required");
  if (folder !== EStorageFolders.profilePic) throw new Error("Unsupported storage folder");
  const fileRef = ref(storage, `users/${uid}/${folder}/${filename}`);
  await uploadBytes(fileRef, file, { contentType: file.type});
  return getDownloadURL(fileRef);
}

/**
 * Uploads a video to Firebase Storage and returns the download URL. 
 */
export async function uploadAnswerVideo(file: File | Blob | ArrayBuffer, interviewId: string) {
  const uid = auth.currentUser?.uid;
  if (!uid) throw new Error("Authentication required");
  const videoRef = ref(storage, `users/${uid}/interview-responses/${interviewId}.mp4`);
  await uploadBytes(videoRef, file, { contentType: "video/mp4"});
  return getDownloadURL(videoRef);
}