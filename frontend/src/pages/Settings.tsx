import { useState, useEffect } from "react";
import { FiArrowLeft, FiLogOut } from "react-icons/fi";
import { useNavigate } from "react-router-dom";
import Header from "../components/Header";
import { grades } from "../utils";
import { userAPI } from "../api/userAPI";

type TabType = "profile" | "courses";

interface PastClass {
  id: string;
  name: string;
  grade?: string;
}

const letterGrades = [
  { value: "A", label: "A" },
  { value: "B", label: "B" },
  { value: "C", label: "C" },
  { value: "D", label: "D" },
  { value: "F", label: "F" },
];

function Settings() {
  const [activeTab, setActiveTab] = useState<TabType>("profile");
  const [grade, setGrade] = useState("");
  const [concentration, setConcentration] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [pastClasses, setPastClasses] = useState<PastClass[]>([]);
  const [currentClassName, setCurrentClassName] = useState("");
  const [currentClassGrade, setCurrentClassGrade] = useState("");
  const [courseError, setCourseError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    // Fetch user data from backend
    const fetchUserData = async () => {
      try {
        setIsLoading(true);
        const user = await userAPI.getUser();
        setGrade(user.grade || "");
        setConcentration(user.concentration || "");

        const pastCourses = await userAPI.getPastCourses();

        const pastClasses = Object.entries(pastCourses["past_courses"]).map(
          ([course, courseGrade]) => {
            const pastClass: PastClass = {
              id: Date.now().toString(),
              name: course.trim().toUpperCase(),
              grade: (courseGrade && typeof courseGrade === 'string') ? courseGrade : undefined,
            };
            return pastClass;
          }
        );

        setPastClasses(pastClasses);

        setError(null);
      } catch (err) {
        console.error("Failed to fetch user data:", err);
        setError("Failed to load user settings. Please try again.");
      } finally {
        setIsLoading(false);
      }
    };

    fetchUserData();
  }, []);

  const handleAddClass = async () => {
    if (!currentClassName.trim()) {
      return;
    }

    const newClass: PastClass = {
      id: Date.now().toString(),
      name: currentClassName.trim().toUpperCase(),
      grade: currentClassGrade || undefined,
    };

    // Create updated list with new class
    const updated = [...pastClasses, newClass];
    // Sort alphabetically by class name
    const sortedCourses = updated.sort((a, b) =>
      a.name.localeCompare(b.name)
    );

    try {
      setCourseError(null);
      const body = {
        past_courses: sortedCourses.reduce<Record<string, string>>(
          (acc, course) => {
            acc[course.name] = course.grade ?? "";
            return acc;
          },
          {}
        ),
      };
      
      // Await the API call
      await userAPI.updatePastCourses(body);
      
      // Only update state if API call succeeds
      setPastClasses(sortedCourses);
      
      // Reset inputs
      setCurrentClassName("");
      setCurrentClassGrade("");
    } catch (ex) {
      console.error("Failed to update past courses:", ex);
      // Show error popup
      setCourseError("This is not a course");
      // Auto-dismiss error after 5 seconds
      setTimeout(() => setCourseError(null), 5000);
      // Don't update state, so the course is not added
    }
  };

  const handleRemoveClass = async (courseCode: string) => {
    const removedClasses = pastClasses.filter((cls) => cls.name !== courseCode);
    try {
        // Await the API call
        const body = {
            past_courses: removedClasses.reduce<Record<string, string>>(
              (acc, course) => {
                acc[course.name] = course.grade ?? "";
                return acc;
              },
              {}
            ),
          };
        await userAPI.updatePastCourses(body);
        setPastClasses(removedClasses);
    } catch (ex) {
        console.error("Failed to delete past courses:", ex);
        // Show error popup
        setCourseError("Failed to delete a course");
        // Auto-dismiss error after 5 seconds
        setTimeout(() => setCourseError(null), 5000);
        // Don't update state, so the course is not added
      }
  };

  const handleSave = async () => {
    try {
      setIsSaving(true);
      setError(null);
      setSuccess(false);

      await userAPI.updateUser({
        grade: grade || undefined,
        concentration: concentration || undefined,
      });

      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      console.error("Failed to save settings:", err);
      setError("Failed to save settings. Please try again.");
    } finally {
      setIsSaving(false);
    }
  };

  const handleBackToChat = () => {
    navigate("/");
  };

  return (
    <div className="app">
      <Header messages={[]} />
      <div className="settings-container">
        <div className="settings-card">
          <div className="settings-header">
            <h1 className="settings-title">Settings</h1>
            <p className="settings-subtitle">Let Tiggy know more about you!</p>
          </div>

          <div className="settings-tabs">
            <button
              className={`settings-tab ${
                activeTab === "profile" ? "active" : ""
              }`}
              onClick={() => setActiveTab("profile")}
            >
              Profile
            </button>
            <button
              className={`settings-tab ${
                activeTab === "courses" ? "active" : ""
              }`}
              onClick={() => setActiveTab("courses")}
            >
              Input Courses
            </button>
          </div>

          <div className="settings-content">
            {activeTab === "profile" && (
              <>
                {isLoading ? (
                  <div style={{ textAlign: "center", padding: "2rem" }}>
                    <p>Loading settings...</p>
                  </div>
                ) : (
                  <>
                    {error && (
                      <div
                        style={{
                          background: "rgba(239, 68, 68, 0.1)",
                          color: "#ef4444",
                          padding: "1rem",
                          borderRadius: "0.75rem",
                          marginBottom: "1rem",
                          border: "1px solid rgba(239, 68, 68, 0.2)",
                        }}
                      >
                        {error}
                      </div>
                    )}
                    {success && (
                      <div
                        style={{
                          background: "rgba(34, 197, 94, 0.1)",
                          color: "#22c55e",
                          padding: "1rem",
                          borderRadius: "0.75rem",
                          marginBottom: "1rem",
                          border: "1px solid rgba(34, 197, 94, 0.2)",
                        }}
                      >
                        Settings saved successfully!
                      </div>
                    )}
                    <div className="settings-section">
                      <h2 className="section-title">Profile Preferences</h2>

                      <div className="form-group">
                        <label htmlFor="grade" className="form-label">
                          Academic Year
                        </label>
                        <select
                          id="grade"
                          value={grade}
                          onChange={(e) => setGrade(e.target.value)}
                          className="form-select"
                          disabled={isSaving}
                        >
                          <option value="">Select your year</option>
                          {grades.map((g) => (
                            <option key={g.value} value={g.value}>
                              {g.label}
                            </option>
                          ))}
                        </select>
                      </div>

                      <div className="form-group">
                        <label htmlFor="concentration" className="form-label">
                          Concentration (Optional)
                        </label>
                        <input
                          type="text"
                          id="concentration"
                          value={concentration}
                          onChange={(e) => setConcentration(e.target.value)}
                          placeholder="e.g., Computer Science, Mathematics"
                          className="form-input"
                          disabled={isSaving}
                        />
                      </div>
                    </div>

                    <div className="settings-actions">
                      <button
                        className="save-button"
                        onClick={handleSave}
                        disabled={isSaving}
                      >
                        {isSaving ? "Saving..." : "Save Changes"}
                      </button>
                    </div>
                  </>
                )}
              </>
            )}

            {activeTab === "courses" && (
              <div className="settings-section">
                <h2 className="section-title">Input Courses</h2>

                {courseError && (
                  <div
                    style={{
                      background: "rgba(239, 68, 68, 0.1)",
                      color: "#ef4444",
                      padding: "1rem",
                      borderRadius: "0.75rem",
                      marginBottom: "1rem",
                      border: "1px solid rgba(239, 68, 68, 0.2)",
                    }}
                  >
                    {courseError}
                  </div>
                )}

                <div className="add-class-form">
                  <div className="add-class-inputs">
                    <input
                      type="text"
                      className="form-input"
                      placeholder="Enter class name (e.g., COS234)"
                      value={currentClassName}
                      onChange={(e) => {
                        setCurrentClassName(e.target.value);
                        // Clear error when user starts typing
                        if (courseError) {
                          setCourseError(null);
                        }
                      }}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") {
                          handleAddClass();
                        }
                      }}
                    />
                    <select
                      className="form-select class-grade-select"
                      value={currentClassGrade}
                      onChange={(e) => setCurrentClassGrade(e.target.value)}
                    >
                      <option value="">Grade (Optional)</option>
                      {letterGrades.map((g) => (
                        <option key={g.value} value={g.value}>
                          {g.label}
                        </option>
                      ))}
                    </select>
                    <button
                      className="add-class-button"
                      onClick={handleAddClass}
                      disabled={!currentClassName.trim()}
                    >
                      Add Class
                    </button>
                  </div>
                </div>

                {pastClasses.length > 0 && (
                  <div className="past-classes-list">
                    <h3 className="past-classes-title">Your Classes</h3>
                    <div className="past-classes-container">
                      {pastClasses.map((cls) => (
                        <div key={cls.id} className="past-class-item">
                          <div className="past-class-info">
                            <span className="past-class-name">{cls.name}</span>
                            {cls.grade && (
                              <span className="past-class-grade">
                                {cls.grade}
                              </span>
                            )}
                          </div>
                          <button
                            className="remove-class-button"
                            onClick={() => handleRemoveClass(cls.name)}
                            aria-label="Remove class"
                          >
                            x
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            <div className="settings-actions">
              <button
                className="back-to-chat-button"
                onClick={handleBackToChat}
              >
                <FiArrowLeft />
                Back to Chat
              </button>
              <button className="logout-button">
                <FiLogOut />
                Logout
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Settings;
