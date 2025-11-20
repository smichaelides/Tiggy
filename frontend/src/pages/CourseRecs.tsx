import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import Header from "../components/Header";
import { userAPI } from "../api/userAPI";
import { recommendationsAPI } from "../api/recommendationsAPI";
import type { User, Course } from "../types";

function CourseRecs() {
  const [user, setUser] = useState<User | null>(null);
  const [courses, setCourses] = useState<Course[] | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchUser = async () => {
      try {
        const userData = await userAPI.getUser();
        setUser(userData);
      } catch (error) {
        console.log("Could not fetch user name (optional):", error);
      }
    };
    fetchUser();
  }, []);

  useEffect(() => {
    const fetchRecommendations = async () => {
      setIsLoading(true);
      setError(null);
      setMessage(null);
      
      try {
        const response = await recommendationsAPI.getCourseRecommendations();
        setCourses(response.courses);
        if (response.message) {
          setMessage(response.message);
        }
      } catch (err) {
        console.error("Failed to fetch recommendations:", err);
        setError(err instanceof Error ? err.message : "Failed to load course recommendations. Please try again later.");
        setCourses(null);
      } finally {
        setIsLoading(false);
      }
    };

    fetchRecommendations();
  }, []);

  return (
    <div className="app">
      <Header messages={[]} />
      <div className="course-recs-container">
        <div className="course-recs-card">
          <div className="course-recs-header">
            <h1 className="course-recs-title">
              Tiggy recommends these courses{user?.name ? ` for you, ${user.name.split(' ')[0]}` : ''}
            </h1>
          </div>

          {/* Message banner for adding past courses */}
          {message && (
            <div className="course-message-banner" style={{
              backgroundColor: '#fff3cd',
              border: '1px solid #ffc107',
              borderRadius: '8px',
              padding: '16px',
              marginBottom: '24px',
              color: '#856404'
            }}>
              <p style={{ margin: 0, marginBottom: '8px' }}>{message}</p>
              <button
                onClick={() => navigate('/settings')}
                style={{
                  backgroundColor: '#ffc107',
                  color: '#000',
                  border: 'none',
                  borderRadius: '4px',
                  padding: '8px 16px',
                  cursor: 'pointer',
                  fontWeight: '500'
                }}
              >
                Go to Settings
              </button>
            </div>
          )}

          {/* Loading state */}
          {isLoading && (
            <div style={{ textAlign: 'center', padding: '40px' }}>
              <p>Loading recommendations...</p>
            </div>
          )}

          {/* Error state */}
          {error && !isLoading && (
            <div style={{
              backgroundColor: '#f8d7da',
              border: '1px solid #f5c6cb',
              borderRadius: '8px',
              padding: '16px',
              marginBottom: '24px',
              color: '#721c24'
            }}>
              <p style={{ margin: 0, marginBottom: '8px' }}>{error}</p>
              <button
                onClick={() => {
                  setError(null);
                  setIsLoading(true);
                  recommendationsAPI.getCourseRecommendations()
                    .then(response => {
                      setCourses(response.courses);
                      if (response.message) {
                        setMessage(response.message);
                      }
                      setIsLoading(false);
                    })
                    .catch(err => {
                      setError(err instanceof Error ? err.message : "Failed to load recommendations");
                      setIsLoading(false);
                    });
                }}
                style={{
                  backgroundColor: '#dc3545',
                  color: '#fff',
                  border: 'none',
                  borderRadius: '4px',
                  padding: '8px 16px',
                  cursor: 'pointer'
                }}
              >
                Retry
              </button>
            </div>
          )}

          {/* Courses list */}
          {!isLoading && !error && courses && courses.length > 0 && (
            <div className="courses-container">
              {courses.map((course, index) => (
                <div key={index} className="course-card">
                  <div className="course-header">
                    <div className="course-code">{course.code}</div>
                    <div className="course-format">{course.format}</div>
                  </div>
                  <h2 className="course-title">{course.title}</h2>
                  <div className="course-details">
                    <div className="course-detail-item">
                      <span className="course-detail-label">Instructor:</span>
                      <span className="course-detail-value">{course.instructor}</span>
                    </div>
                    <div className="course-detail-item">
                      <span className="course-detail-label">Schedule:</span>
                      <span className="course-detail-value">{course.schedule}</span>
                    </div>
                  </div>
                  <p className="course-description">{course.description}</p>
                </div>
              ))}
            </div>
          )}

          {/* Empty state */}
          {!isLoading && !error && (!courses || courses.length === 0) && (
            <div style={{ textAlign: 'center', padding: '40px' }}>
              <p>No course recommendations available at this time.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default CourseRecs;
