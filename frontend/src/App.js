import React, { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Language translations
const translations = {
  en: {
    appTitle: "Remind Me Important",
    addNote: "Add Note",
    textNote: "Text Note",
    voiceNote: "Voice Note",
    title: "Title",
    content: "Content",
    category: "Category",
    setReminder: "Set Reminder",
    save: "Save",
    cancel: "Cancel",
    delete: "Delete",
    edit: "Edit",
    play: "Play",
    stop: "Stop",
    record: "Record",
    recording: "Recording...",
    categories: {
      personal: "Personal",
      work: "Work",
      study: "Study",
      shopping: "Shopping",
      health: "Health",
      other: "Other"
    },
    stats: {
      total: "Total Notes",
      text: "Text Notes", 
      audio: "Audio Notes",
      completed: "Completed",
      reminders: "Pending Reminders"
    },
    noNotes: "No notes yet. Create your first note!",
    permissionDenied: "Microphone permission denied",
    notSupported: "Voice recording not supported"
  },
  ar: {
    appTitle: "ذكّرني بالمهم",
    addNote: "إضافة ملاحظة",
    textNote: "ملاحظة نصية",
    voiceNote: "ملاحظة صوتية",
    title: "العنوان",
    content: "المحتوى",
    category: "التصنيف",
    setReminder: "تعيين تذكير",
    save: "حفظ",
    cancel: "إلغاء",
    delete: "حذف",
    edit: "تعديل",
    play: "تشغيل",
    stop: "إيقاف",
    record: "تسجيل",
    recording: "جاري التسجيل...",
    categories: {
      personal: "شخصي",
      work: "عمل",
      study: "دراسة",
      shopping: "تسوق",
      health: "صحة",
      other: "أخرى"
    },
    stats: {
      total: "إجمالي الملاحظات",
      text: "الملاحظات النصية",
      audio: "الملاحظات الصوتية", 
      completed: "المكتملة",
      reminders: "التذكيرات المعلقة"
    },
    noNotes: "لا توجد ملاحظات بعد. أنشئ ملاحظتك الأولى!",
    permissionDenied: "تم رفض إذن الميكروفون",
    notSupported: "التسجيل الصوتي غير مدعوم"
  }
};

function App() {
  const [language, setLanguage] = useState('ar');
  const [notes, setNotes] = useState([]);
  const [stats, setStats] = useState({});
  const [showAddForm, setShowAddForm] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [isRecording, setIsRecording] = useState(false);
  const [mediaRecorder, setMediaRecorder] = useState(null);
  const [audioChunks, setAudioChunks] = useState([]);
  const [currentAudio, setCurrentAudio] = useState(null);

  const t = translations[language];

  // Form state
  const [formData, setFormData] = useState({
    title: '',
    content: '',
    note_type: 'text',
    category: 'personal',
    reminder_time: '',
    audio_data: '',
    audio_duration: 0
  });

  useEffect(() => {
    fetchNotes();
    fetchStats();
    requestNotificationPermission();
  }, [selectedCategory]);

  const requestNotificationPermission = async () => {
    if ('Notification' in window && Notification.permission === 'default') {
      await Notification.requestPermission();
    }
  };

  const fetchNotes = async () => {
    try {
      const response = await axios.get(`${API}/notes?category=${selectedCategory}`);
      setNotes(response.data);
    } catch (error) {
      console.error('Error fetching notes:', error);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API}/stats`);
      setStats(response.data);
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          setAudioChunks(prev => [...prev, event.data]);
        }
      };

      recorder.onstop = () => {
        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
        const reader = new FileReader();
        reader.onloadend = () => {
          const base64Audio = reader.result.split(',')[1];
          setFormData(prev => ({
            ...prev,
            audio_data: base64Audio,
            audio_duration: Math.round(Date.now() / 1000) // Simple duration tracking
          }));
        };
        reader.readAsDataURL(audioBlob);
        
        stream.getTracks().forEach(track => track.stop());
      };

      setMediaRecorder(recorder);
      recorder.start();
      setIsRecording(true);
      setAudioChunks([]);
    } catch (error) {
      console.error('Error starting recording:', error);
      alert(t.permissionDenied);
    }
  };

  const stopRecording = () => {
    if (mediaRecorder && isRecording) {
      mediaRecorder.stop();
      setIsRecording(false);
    }
  };

  const playAudio = (audioData) => {
    if (currentAudio) {
      currentAudio.pause();
    }
    
    const audio = new Audio(`data:audio/webm;base64,${audioData}`);
    audio.play();
    setCurrentAudio(audio);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const noteData = {
        ...formData,
        reminder_time: formData.reminder_time ? new Date(formData.reminder_time).toISOString() : null
      };

      await axios.post(`${API}/notes`, noteData);
      
      // Reset form
      setFormData({
        title: '',
        content: '',
        note_type: 'text',
        category: 'personal',
        reminder_time: '',
        audio_data: '',
        audio_duration: 0
      });
      setShowAddForm(false);
      fetchNotes();
      fetchStats();
    } catch (error) {
      console.error('Error creating note:', error);
    }
  };

  const deleteNote = async (noteId) => {
    try {
      await axios.delete(`${API}/notes/${noteId}`);
      fetchNotes();
      fetchStats();
    } catch (error) {
      console.error('Error deleting note:', error);
    }
  };

  const toggleComplete = async (note) => {
    try {
      await axios.put(`${API}/notes/${note.id}`, {
        is_completed: !note.is_completed
      });
      fetchNotes();
      fetchStats();
    } catch (error) {
      console.error('Error updating note:', error);
    }
  };

  return (
    <div className={`App ${language === 'ar' ? 'rtl' : 'ltr'}`}>
      {/* Header */}
      <header className="app-header">
        <div className="header-content">
          <h1 className="app-title">
            <svg className="note-icon" viewBox="0 0 24 24" fill="currentColor">
              <path d="M20,2H4A2,2 0 0,0 2,4V22L6,18H20A2,2 0 0,0 22,16V4A2,2 0 0,0 20,2M20,16H5.17L4,17.17V4H20V16M7,9H17V11H7V9M7,5H17V7H7V5M7,13H13V15H7V13Z"/>
            </svg>
            {t.appTitle}
          </h1>
          <div className="header-actions">
            <button
              className="lang-toggle"
              onClick={() => setLanguage(language === 'ar' ? 'en' : 'ar')}
            >
              {language === 'ar' ? 'EN' : 'ع'}
            </button>
            <button 
              className="add-note-btn"
              onClick={() => setShowAddForm(!showAddForm)}
            >
              <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M19,13H13V19H11V13H5V11H11V5H13V11H19V13Z"/>
              </svg>
              {t.addNote}
            </button>
          </div>
        </div>
      </header>

      {/* Stats Cards */}
      <div className="stats-container">
        <div className="stats-card stats-card-total">
          <div className="stat-value">{stats.total_notes || 0}</div>
          <div className="stat-label">{t.stats.total}</div>
        </div>
        <div className="stats-card stats-card-text">
          <div className="stat-value">{stats.text_notes || 0}</div>
          <div className="stat-label">{t.stats.text}</div>
        </div>
        <div className="stats-card stats-card-audio">
          <div className="stat-value">{stats.audio_notes || 0}</div>
          <div className="stat-label">{t.stats.audio}</div>
        </div>
        <div className="stats-card stats-card-completed">
          <div className="stat-value">{stats.completed_notes || 0}</div>
          <div className="stat-label">{t.stats.completed}</div>
        </div>
        <div className="stats-card stats-card-reminders">
          <div className="stat-value">{stats.pending_reminders || 0}</div>
          <div className="stat-label">{t.stats.reminders}</div>
        </div>
      </div>

      {/* Category Filter */}
      <div className="category-filter">
        <select 
          value={selectedCategory} 
          onChange={(e) => setSelectedCategory(e.target.value)}
          className="category-select"
        >
          <option value="all">الكل / All</option>
          {Object.entries(t.categories).map(([key, value]) => (
            <option key={key} value={key}>{value}</option>
          ))}
        </select>
      </div>

      {/* Add Note Form */}
      {showAddForm && (
        <div className="modal-overlay" onClick={() => setShowAddForm(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <form onSubmit={handleSubmit} className="note-form">
              <h2>{t.addNote}</h2>
              
              <div className="note-type-toggle">
                <button
                  type="button"
                  className={formData.note_type === 'text' ? 'active' : ''}
                  onClick={() => setFormData(prev => ({...prev, note_type: 'text'}))}
                >
                  {t.textNote}
                </button>
                <button
                  type="button"
                  className={formData.note_type === 'audio' ? 'active' : ''}
                  onClick={() => setFormData(prev => ({...prev, note_type: 'audio'}))}
                >
                  {t.voiceNote}
                </button>
              </div>

              <input
                type="text"
                placeholder={t.title}
                value={formData.title}
                onChange={(e) => setFormData(prev => ({...prev, title: e.target.value}))}
                required
                className="form-input"
              />

              {formData.note_type === 'text' ? (
                <textarea
                  placeholder={t.content}
                  value={formData.content}
                  onChange={(e) => setFormData(prev => ({...prev, content: e.target.value}))}
                  className="form-textarea"
                  rows={4}
                />
              ) : (
                <div className="audio-recording">
                  {!isRecording ? (
                    <button
                      type="button"
                      onClick={startRecording}
                      className="record-btn"
                    >
                      <svg viewBox="0 0 24 24" fill="currentColor">
                        <path d="M12,2A3,3 0 0,1 15,5V11A3,3 0 0,1 12,14A3,3 0 0,1 9,11V5A3,3 0 0,1 12,2M19,11C19,14.53 16.39,17.44 13,17.93V21H11V17.93C7.61,17.44 5,14.53 5,11H7A5,5 0 0,0 12,16A5,5 0 0,0 17,11H19Z"/>
                      </svg>
                      {t.record}
                    </button>
                  ) : (
                    <button
                      type="button"
                      onClick={stopRecording}
                      className="record-btn recording"
                    >
                      <svg viewBox="0 0 24 24" fill="currentColor">
                        <path d="M6,19A2,2 0 0,0 8,21H16A2,2 0 0,0 18,19V7H6V19Z"/>
                      </svg>
                      {t.recording}
                    </button>
                  )}
                  {formData.audio_data && (
                    <button
                      type="button"
                      onClick={() => playAudio(formData.audio_data)}
                      className="play-btn"
                    >
                      <svg viewBox="0 0 24 24" fill="currentColor">
                        <path d="M8,5.14V19.14L19,12.14L8,5.14Z"/>
                      </svg>
                      {t.play}
                    </button>
                  )}
                </div>
              )}

              <select
                value={formData.category}
                onChange={(e) => setFormData(prev => ({...prev, category: e.target.value}))}
                className="form-select"
              >
                {Object.entries(t.categories).map(([key, value]) => (
                  <option key={key} value={key}>{value}</option>
                ))}
              </select>

              <input
                type="datetime-local"
                value={formData.reminder_time}
                onChange={(e) => setFormData(prev => ({...prev, reminder_time: e.target.value}))}
                className="form-input"
                placeholder={t.setReminder}
              />

              <div className="form-actions">
                <button type="submit" className="save-btn">{t.save}</button>
                <button 
                  type="button" 
                  onClick={() => setShowAddForm(false)}
                  className="cancel-btn"
                >
                  {t.cancel}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Notes List */}
      <div className="notes-container">
        {notes.length === 0 ? (
          <div className="empty-state">
            <svg className="empty-icon" viewBox="0 0 24 24" fill="currentColor">
              <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z"/>
            </svg>
            <p>{t.noNotes}</p>
          </div>
        ) : (
          <div className="notes-grid">
            {notes.map(note => (
              <div key={note.id} className={`note-card ${note.is_completed ? 'completed' : ''}`}>
                <div className="note-header">
                  <h3 className="note-title">{note.title}</h3>
                  <div className="note-actions">
                    <button 
                      onClick={() => toggleComplete(note)}
                      className="complete-btn"
                    >
                      <svg viewBox="0 0 24 24" fill="currentColor">
                        <path d={note.is_completed ? "M21,7L9,19L3.5,13.5L4.91,12.09L9,16.17L19.59,5.59L21,7Z" : "M19,3H5C3.89,3 3,3.89 3,5V19A2,2 0 0,0 5,21H19A2,2 0 0,0 21,19V5C3.89,3 3,3.89 3,5Z"}/>
                      </svg>
                    </button>
                    <button 
                      onClick={() => deleteNote(note.id)}
                      className="delete-btn"
                    >
                      <svg viewBox="0 0 24 24" fill="currentColor">
                        <path d="M19,4H15.5L14.5,3H9.5L8.5,4H5V6H19M6,19A2,2 0 0,0 8,21H16A2,2 0 0,0 18,19V7H6V19Z"/>
                      </svg>
                    </button>
                  </div>
                </div>
                
                <div className="note-content">
                  {note.note_type === 'text' ? (
                    <p>{note.content}</p>
                  ) : (
                    <div className="audio-note">
                      <button
                        onClick={() => playAudio(note.audio_data)}
                        className="play-audio-btn"
                      >
                        <svg viewBox="0 0 24 24" fill="currentColor">
                          <path d="M8,5.14V19.14L19,12.14L8,5.14Z"/>
                        </svg>
                        {t.play}
                      </button>
                    </div>
                  )}
                </div>
                
                <div className="note-meta">
                  <span className="category-badge">{t.categories[note.category]}</span>
                  {note.reminder_time && (
                    <span className="reminder-time">
                      <svg viewBox="0 0 24 24" fill="currentColor">
                        <path d="M12,20A8,8 0 0,0 20,12A8,8 0 0,0 12,4A8,8 0 0,0 4,12A8,8 0 0,0 12,20M12,2A10,10 0 0,1 22,12A10,10 0 0,1 12,22C6.47,22 2,17.5 2,12A10,10 0 0,1 12,2M12.5,7V12.25L17,14.92L16.25,16.15L11,13V7H12.5Z"/>
                      </svg>
                      {new Date(note.reminder_time).toLocaleDateString(language === 'ar' ? 'ar-SA' : 'en-US')}
                    </span>
                  )}
                  <span className="note-date">
                    {new Date(note.created_at).toLocaleDateString(language === 'ar' ? 'ar-SA' : 'en-US')}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;