// Princeton academic data
export const grades = [
    { value: 'freshman', label: 'Freshman' },
    { value: 'sophomore', label: 'Sophomore' },
    { value: 'junior', label: 'Junior' },
    { value: 'senior', label: 'Senior' }
];

export const princetonMajors = [
    { value: 'aas', label: 'African American Studies' },
    { value: 'ant', label: 'Anthropology' },
    { value: 'arc', label: 'Architecture' },
    { value: 'art', label: 'Art and Archaeology' },
    { value: 'ast', label: 'Astrophysical Sciences' },
    { value: 'che', label: 'Chemical and Biological Engineering' },
    { value: 'chi', label: 'Chemistry' },
    { value: 'civ', label: 'Civil and Environmental Engineering' },
    { value: 'cla', label: 'Classics' },
    { value: 'com', label: 'Comparative Literature' },
    { value: 'cos', label: 'Computer Science' },
    { value: 'eas', label: 'East Asian Studies' },
    { value: 'eco', label: 'Economics' },
    { value: 'ele', label: 'Electrical and Computer Engineering' },
    { value: 'eng', label: 'English' },
    { value: 'frs', label: 'French and Italian' },
    { value: 'geo', label: 'Geosciences' },
    { value: 'ger', label: 'German' },
    { value: 'his', label: 'History' },
    { value: 'mat', label: 'Mathematics' },
    { value: 'mec', label: 'Mechanical and Aerospace Engineering' },
    { value: 'mol', label: 'Molecular Biology' },
    { value: 'mus', label: 'Music' },
    { value: 'nea', label: 'Near Eastern Studies' },
    { value: 'neu', label: 'Neuroscience' },
    { value: 'ope', label: 'Operations Research and Financial Engineering' },
    { value: 'phi', label: 'Philosophy' },
    { value: 'phy', label: 'Physics' },
    { value: 'pol', label: 'Politics' },
    { value: 'psy', label: 'Psychology' },
    { value: 'rel', label: 'Religion' },
    { value: 'sls', label: 'Slavic Languages and Literatures' },
    { value: 'soc', label: 'Sociology' },
    { value: 'spa', label: 'Spanish and Portuguese' },
    { value: 'wri', label: 'Writing' }
];

// Settings interface
export interface UserSettings {
    grade: string;
    major: string;
    concentration: string;
}

// Settings storage functions
export const saveUserSettings = (settings: UserSettings): void => {
};

export const loadUserSettings = (): UserSettings => {
    if (savedSettings) {
        try {
            return JSON.parse(savedSettings);
        } catch (error) {
            console.error('Error parsing saved settings:', error);
        }
    }
    return { grade: '', major: '', concentration: '' };
};

export const clearUserSettings = (): void => {
}; 