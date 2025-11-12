import { useState, useEffect } from 'react';
import { FiArrowLeft, FiLogOut } from 'react-icons/fi';
import { useNavigate } from 'react-router-dom';
import Header from '../components/Header';
import { grades } from '../utils';
import { userAPI } from '../api/userAPI';

function Settings() {
    const [grade, setGrade] = useState('');
    const [concentration, setConcentration] = useState('');
    const [isLoading, setIsLoading] = useState(true);
    const [isSaving, setIsSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState(false);
    const navigate = useNavigate();

    useEffect(() => {
        // Fetch user data from backend
        const fetchUserData = async () => {
            try {
                setIsLoading(true);
                const user = await userAPI.getUser();
                setGrade(user.grade || '');
                setConcentration(user.concentration || '');
                setError(null);
            } catch (err) {
                console.error('Failed to fetch user data:', err);
                setError('Failed to load user settings. Please try again.');
            } finally {
                setIsLoading(false);
            }
        };

        fetchUserData();
    }, []);

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
            console.error('Failed to save settings:', err);
            setError('Failed to save settings. Please try again.');
        } finally {
            setIsSaving(false);
        }
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
                        {isLoading ? (
                            <div style={{ textAlign: 'center', padding: '2rem' }}>
                                <p>Loading settings...</p>
                            </div>
                        ) : (
                            <>
                                {error && (
                                    <div style={{ 
                                        background: 'rgba(239, 68, 68, 0.1)', 
                                        color: '#ef4444', 
                                        padding: '1rem', 
                                        borderRadius: '0.75rem', 
                                        marginBottom: '1rem',
                                        border: '1px solid rgba(239, 68, 68, 0.2)'
                                    }}>
                                        {error}
                                    </div>
                                )}
                                {success && (
                                    <div style={{ 
                                        background: 'rgba(34, 197, 94, 0.1)', 
                                        color: '#22c55e', 
                                        padding: '1rem', 
                                        borderRadius: '0.75rem', 
                                        marginBottom: '1rem',
                                        border: '1px solid rgba(34, 197, 94, 0.2)'
                                    }}>
                                        Settings saved successfully!
                                    </div>
                                )}
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
                                        <label htmlFor="concentration" className="form-label">Concentration (Optional)</label>
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
                                        {isSaving ? 'Saving...' : 'Save Changes'}
                                    </button>
                                </div>
                            </>
                        )}
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