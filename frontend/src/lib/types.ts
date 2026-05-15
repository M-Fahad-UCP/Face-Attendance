export type User = {
  id: number;
  username: string;
  full_name: string;
  role: "admin" | "user";
  department: string;
};

export type FaceBox = {
  bbox: number[];
  username: string;
  score: number;
  matched: boolean;
};

export type RecognizeResult = {
  faces: FaceBox[];
  primary_username: string;
  threshold: number;
  preview_base64?: string | null;
};

export type AttendanceRecord = {
  username: string;
  full_name: string;
  date: string;
  time: string;
  department?: string;
  member_role?: string;
  record_status?: string;
};

export type Member = {
  id: number;
  username: string;
  full_name: string;
  department: string;
  has_face_template: boolean;
};
