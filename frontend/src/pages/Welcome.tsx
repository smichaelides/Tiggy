import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import princetonLogo from '../assets/princeton.png';
import tigerAvatar from '../assets/tiggy.png';
import { princetonMajors, grades } from '../utils/settings';

function Welcome() {
  const [currentStep, setCurrentStep] = useState(1);
  const [userData, setUserData] = useState({
    grade: '',
    concentration: '',
    favoriteClasses: [] as string[]
  });
  const [tempClass, setTempClass] = useState('');
  const navigate = useNavigate();

  const totalSteps = 3;

  const handleNext = () => {
    if (currentStep < totalSteps) {
      setCurrentStep(currentStep + 1);
    } else {
      navigate("/");
    }
  };

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const addFavoriteClass = () => {
    if (tempClass.trim() && !userData.favoriteClasses.includes(tempClass.trim())) {
      setUserData(prev => ({
        ...prev,
        favoriteClasses: [...prev.favoriteClasses, tempClass.trim()]
      }));
      setTempClass('');
    }
  };

  const removeFavoriteClass = (index: number) => {
    setUserData(prev => ({
      ...prev,
      favoriteClasses: prev.favoriteClasses.filter((_, i) => i !== index)
    }));
  };

  const canProceed = () => {
    switch (currentStep) {
      case 1:
        return userData.grade !== '';
      case 2:
        return userData.concentration !== '';
      case 3:
        return true; // Optional step
      default:
        return false;
    }
  };

  const renderStep = () => {
    switch (currentStep) {
      case 1:
        return (
          <div className="welcome-page-step">
            <h2 className="welcome-page-step-title">What's your class year?</h2>
            <p className="welcome-page-step-subtitle">This helps Tiggy understand your academic journey</p>
            <div className="welcome-page-options">
              {grades.map((grade) => (
                <button
                  key={grade.value}
                  className={`welcome-page-option ${userData.grade === grade.value ? 'selected' : ''}`}
                  onClick={() => setUserData(prev => ({ ...prev, grade: grade.value }))}
                >
                  {grade.label}
                </button>
              ))}
            </div>
          </div>
        );

      case 2:
        return (
          <div className="welcome-page-step">
            <h2 className="welcome-page-step-title">What's your concentration?</h2>
            <p className="welcome-page-step-subtitle">Choose your primary field of study</p>
            <div className="welcome-page-select-container">
              <select
                className="welcome-page-select"
                value={userData.concentration}
                onChange={(e) => setUserData(prev => ({ ...prev, concentration: e.target.value }))}
              >
                <option value="">Select your concentration...</option>
                {princetonMajors.map((major) => (
                  <option key={major.value} value={major.value}>
                    {major.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
        );

      case 3:
        return (
          <div className="welcome-page-step">
            <h2 className="welcome-page-step-title">What are your favorite classes?</h2>
            <p className="welcome-page-step-subtitle">Add classes you've enjoyed or are looking forward to (optional)</p>
            <div className="welcome-page-input-container">
              <input
                type="text"
                className="welcome-page-input"
                placeholder="Enter a class name..."
                value={tempClass}
                onChange={(e) => setTempClass(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && addFavoriteClass()}
              />
              <button className="welcome-page-add-btn" onClick={addFavoriteClass}>
                Add
              </button>
            </div>
            <div className="welcome-page-tags">
              {userData.favoriteClasses.map((className, index) => (
                <span key={index} className="welcome-page-tag">
                  {className}
                  <button 
                    className="welcome-page-tag-remove"
                    onClick={() => removeFavoriteClass(index)}
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="welcome-page-container">
      <div className="welcome-page-card">
        <div className="welcome-page-header">
          <img src={princetonLogo} alt="Princeton" className="welcome-page-logo" />
          <div className="welcome-page-title-container">
            <h1 className="welcome-page-title">Welcome to Tiggy!</h1>
            <img src={tigerAvatar} alt="Tiggy" className="welcome-page-tiggy" />
          </div>
          <p className="welcome-page-subtitle">Let's get to know you better</p>
        </div>

        <div className="welcome-page-progress">
          <div className="welcome-page-progress-bar">
            <div 
              className="welcome-page-progress-fill" 
              style={{ width: `${(currentStep / totalSteps) * 100}%` }}
            />
          </div>
          <span className="welcome-page-progress-text">
            Step {currentStep} of {totalSteps}
          </span>
        </div>

        <div className="welcome-page-content">
          {renderStep()}
        </div>

        <div className="welcome-page-actions">
          {currentStep > 1 && (
            <button 
              className="welcome-page-btn welcome-page-btn-secondary" 
              onClick={handleBack}
            >
              Back
            </button>
          )}
          
          <button 
            className="welcome-page-btn welcome-page-btn-primary" 
            onClick={handleNext}
            disabled={!canProceed()}
          >
            {currentStep === totalSteps ? 'Get Started' : 'Next'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default Welcome;