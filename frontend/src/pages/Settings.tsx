import { useState, useEffect } from 'react';
import { FiArrowLeft, FiLogOut } from 'react-icons/fi';
import { useNavigate } from 'react-router-dom';
import Header from '../components/Header';
import { grades, princetonMajors, loadUserSettings, saveUserSettings, type UserSettings } from '../utils';

function Settings() {
    const [grade, setGrade] = useState('');
    const [major, setMajor] = useState('');
    const [concentration, setConcentration] = useState('');
    const navigate = useNavigate();

    useEffect(() => {
        // Load saved settings (TEMPORARY)
        const savedSettings = loadUserSettings();
        setGrade(savedSettings.grade);
        setMajor(savedSettings.major);
        setConcentration(savedSettings.concentration);
    }, []);

    const handleSave = () => {
        const settings: UserSettings = { grade, major, concentration };
        saveUserSettings(settings);
        console.log('Settings saved:', settings);
    };

    const handleBackToChat = () => {
        navigate('/');
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
                    
                    <div className="settings-content">
                        <div className="settings-section">
                            <h2 className="section-title">
                                Profile Preferences
                            </h2>
                            
                            <div className="form-group">
                                <label htmlFor="grade" className="form-label">Academic Year</label>
                                <select
                                    id="grade"
                                    value={grade}
                                    onChange={(e) => setGrade(e.target.value)}
                                    className="form-select"
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
                                <label htmlFor="major" className="form-label">Major</label>
                                <select
                                    id="major"
                                    value={major}
                                    onChange={(e) => setMajor(e.target.value)}
                                    className="form-select"
                                >
                                    <option value="">Select your major</option>
                                    {princetonMajors.map((m) => (
                                        <option key={m.value} value={m.value}>
                                            {m.label}
                                        </option>
                                    ))}
                                </select>
                            </div>

                            <div className="form-group">
                                <label htmlFor="concentration" className="form-label">Concentration (Optional)</label>
                                <input
                                    type="text"
                                    id="concentration"
                                    value={concentration}
                                    onChange={(e) => setConcentration(e.target.value)}
                                    placeholder="e.g., Computer Science, Mathematics"
                                    className="form-input"
                                />
                            </div>
                        </div>

                        <div className="settings-actions">
                            <button className="save-button" onClick={handleSave}>
                                Save Changes
                            </button>
                        </div>
                        <div className="settings-actions">
                            <button className="back-to-chat-button" 
                                onClick={handleBackToChat}>
                                <FiArrowLeft />
                                Back to Chat
                            </button>
                            <button 
                                className="logout-button"
                            >
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