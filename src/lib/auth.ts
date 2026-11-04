import { SignJWT, jwtVerify } from "jose";
import { cookies } from "next/headers";
const secret = new TextEncoder().encode(process.env.JWT_SECRET || "development-only-change-this-secret");
export async function createToken(user: {id:string;name:string;email:string}) { return new SignJWT(user).setProtectedHeader({alg:"HS256"}).setIssuedAt().setExpirationTime("7d").sign(secret); }
export async function currentUser() { const jar=await cookies(); const token=jar.get("pypath_token")?.value; if(!token) return null; try { const {payload}=await jwtVerify(token,secret); if(typeof payload.id!=="string") return null; return {id:payload.id,name:String(payload.name||"Learner"),email:String(payload.email||"")}; } catch { return null; } }
export function authCookie(token:string) { return {name:"pypath_token",value:token,httpOnly:true,secure:process.env.NODE_ENV==="production",sameSite:"lax" as const,path:"/",maxAge:60*60*24*7}; }
