import type { OnboardingInfo, User } from '../types';
import { apiRequest } from '../utils/api';

interface GoogleUserInfo {
    sub: string;
    name: string;
    email: string;
    picture?: string;
}

export const authAPI = {
    login: async (email: string): Promise<{ user: User }> => {
        return apiRequest<{ user: User }>('/auth/login', {
            method: 'POST',
            body: JSON.stringify({email})
        });
    },

    completeUserLogin: async (userData: OnboardingInfo): Promise<{ user: User }> => {
        return apiRequest<{ user: User }>('/auth/complete-user-login', {
            method: 'POST',
            body: JSON.stringify({ userData })
        })
    },

    // external APIs
    googleLogin: async (accessToken: string): Promise<GoogleUserInfo> => {
        const userInfoResponse = await fetch(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            {
                headers: {
                    Authorization: `Bearer ${accessToken}`,
                },
            }
        );

        if (!userInfoResponse.ok) {
            throw new Error(`Failed to fetch user info: ${userInfoResponse.status}`);
        }

        return userInfoResponse.json();
    },
};