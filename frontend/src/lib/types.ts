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
  check_out_time?: string;
  status?: string;
  record_status?: string;
  department?: string;
  member_role?: string;
};

export type Member = {
  id: number;
  username: string;
  full_name: string;
  department: string;
  has_face_template: boolean;
};

export type UserDashboard = {
  username: string;
  full_name: string;
  checked_in_today: boolean;
  checked_out_today: boolean;
  check_in_time: string;
  check_out_time: string;
};
