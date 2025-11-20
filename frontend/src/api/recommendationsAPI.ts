import type { RecommendationsResponse } from '../types';
import { apiRequest } from '../utils/api';

// Recommendations API functions
export const recommendationsAPI = {
  getCourseRecommendations: async (): Promise<RecommendationsResponse> => {
    return apiRequest<RecommendationsResponse>('/recommendations/courses');
  }
};
