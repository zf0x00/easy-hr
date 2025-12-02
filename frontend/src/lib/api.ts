import axios from "axios";

export const api = axios.create({
  baseURL: "http://localhost:8000",
});

export const getChats = async () => {
  const response = await api.get("/api/chats");
  return response.data;
};

export const getChat = async (id: string) => {
  const response = await api.get(`/api/chats/${id}`);
  return response.data;
};

export const createChat = async (messages: any[]) => {
  const response = await api.post("/api/chats", { messages });
  return response.data;
};

export const addMessages = async (chatId: string, messages: any[]) => {
  const response = await api.post(`/api/chats/${chatId}/messages`, { messages });
  return response.data;
};