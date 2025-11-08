// Chat API functions
interface GoogleUserInfo {
    sub: string;
    name: string;
    email: string;
    picture?: string;
}

export const authAPI = {
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