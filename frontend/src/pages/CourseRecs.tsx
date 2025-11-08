import { useState, useEffect } from "react";
import Header from "../components/Header";
import { userAPI } from "../api/userAPI";
import type { User } from "../types";

interface Course {
  code: string;
  title: string;
  instructor: string;
  format: string;
  schedule: string;
  description: string;
}

function CourseRecs() {
  const [user, setUser] = useState<User | null>(null);

  // Example courses - replace with API call later
  const [courseRecs] = useState<Course[]>([
    {
      code: "AAS 225",
      title: "Martin, Malcolm, and Ella",
      instructor: "Eddie S. Glaude",
      format: "Seminar",
      schedule: "Tues 1:30-4:20 PM | Morrison Hall 104",
      description: "Examines Black Freedom Movement leadership."
    },
    {
      code: "COS 126",
      title: "Computer Science: An Interdisciplinary Approach",
      instructor: "Robert Sedgewick",
      format: "Lecture",
      schedule: "Mon, Wed 10:00-10:50 AM | Friend Center 101",
      description: "An introduction to computer science in the context of scientific, engineering, and commercial applications. Topics include algorithms, data structures, and computer systems."
    },
    {
      code: "ECO 100",
      title: "Introduction to Microeconomics",
      instructor: "Harold H. Kuhn",
      format: "Lecture",
      schedule: "Mon, Wed, Fri 11:00-11:50 AM | McCosh Hall 50",
      description: "Introduction to economic analysis and its applications. Topics include supply and demand, market structures, consumer choice, and firm behavior."
    },
    {
      code: "HIS 300",
      title: "The American Revolution",
      instructor: "Sean Wilentz",
      format: "Seminar",
      schedule: "Thurs 1:30-4:20 PM | Dickinson Hall 211",
      description: "An in-depth examination of the causes, course, and consequences of the American Revolution, with emphasis on political, social, and intellectual developments."
    },
    {
      code: "PHI 201",
      title: "Introduction to Philosophy",
      instructor: "Gideon Rosen",
      format: "Lecture",
      schedule: "Tue, Thu 10:00-10:50 AM | McCosh Hall 28",
      description: "An introduction to fundamental philosophical questions concerning knowledge, reality, ethics, and the nature of mind. Readings from classical and contemporary sources."
    }
  ]);

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

  return (
    <div className="app">
      <Header messages={[]} />
      <div className="course-recs-container">
        <div className="course-recs-card">
          <div className="course-recs-header">
            <h1 className="course-recs-title">
              Tiggy recommends these courses{user?.name ? ` for you, ${user.name}` : ''}
            </h1>
          </div>
          
          <div className="courses-container">
            {/* Courses will be mapped here */}
          </div>
        </div>
      </div>
    </div>
  );
}

export default CourseRecs;
