import React, { useState, useEffect } from 'react';
import {
  Text,
  View,
  StyleSheet,
  ScrollView,
  TextInput,
  TouchableOpacity,
  Alert,
  Platform,
  KeyboardAvoidingView,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';

const EXPO_PUBLIC_BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

interface Language {
  code: string;
  name: string;
  native_name: string;
}

interface Translation {
  id: string;
  original_text: string;
  translated_text: string;
  source_language: string;
  target_language: string;
  timestamp: string;
  confidence_score?: number;
}

export default function TranslationApp() {
  const router = useRouter();
  
  // State management
  const [inputText, setInputText] = useState('');
  const [translatedText, setTranslatedText] = useState('');
  const [sourceLanguage, setSourceLanguage] = useState('auto');
  const [targetLanguage, setTargetLanguage] = useState('en');
  const [languages, setLanguages] = useState<Language[]>([]);
  const [isTranslating, setIsTranslating] = useState(false);
  const [recentTranslations, setRecentTranslations] = useState<Translation[]>([]);
  const [showLanguageSelector, setShowLanguageSelector] = useState<'source' | 'target' | null>(null);

  // Fetch supported languages on component mount
  useEffect(() => {
    fetchLanguages();
    fetchRecentTranslations();
  }, []);

  const fetchLanguages = async () => {
    try {
      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/languages`);
      if (response.ok) {
        const data = await response.json();
        setLanguages(data);
      }
    } catch (error) {
      console.error('Error fetching languages:', error);
    }
  };

  const fetchRecentTranslations = async () => {
    try {
      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/translate/history`);
      if (response.ok) {
        const data = await response.json();
        setRecentTranslations(data.slice(0, 5)); // Show only recent 5
      }
    } catch (error) {
      console.error('Error fetching recent translations:', error);
    }
  };

  const translateText = async () => {
    if (!inputText.trim()) {
      Alert.alert('Error', 'Please enter text to translate');
      return;
    }

    setIsTranslating(true);
    try {
      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/translate/text`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text: inputText,
          source_language: sourceLanguage,
          target_language: targetLanguage,
        }),
      });

      if (response.ok) {
        const translation = await response.json();
        setTranslatedText(translation.translated_text);
        fetchRecentTranslations(); // Refresh recent translations
      } else {
        const error = await response.json();
        Alert.alert('Translation Error', error.detail || 'Failed to translate text');
      }
    } catch (error) {
      console.error('Translation error:', error);
      Alert.alert('Error', 'Network error. Please try again.');
    } finally {
      setIsTranslating(false);
    }
  };

  const swapLanguages = () => {
    if (sourceLanguage === 'auto') {
      Alert.alert('Cannot Swap', 'Cannot swap when source language is set to auto-detect');
      return;
    }
    
    const newSource = targetLanguage;
    const newTarget = sourceLanguage;
    setSourceLanguage(newSource);
    setTargetLanguage(newTarget);
    
    // Swap texts if both exist
    if (inputText && translatedText) {
      setInputText(translatedText);
      setTranslatedText(inputText);
    }
  };

  const getLanguageName = (code: string) => {
    if (code === 'auto') return 'Auto Detect';
    const language = languages.find(lang => lang.code === code);
    return language ? language.name : code;
  };

  const LanguageSelector = ({ 
    type, 
    currentLanguage, 
    onSelect 
  }: { 
    type: 'source' | 'target';
    currentLanguage: string;
    onSelect: (code: string) => void;
  }) => (
    <View style={styles.languageSelectorContainer}>
      <ScrollView style={styles.languageList}>
        {type === 'source' && (
          <TouchableOpacity
            style={[
              styles.languageOption,
              currentLanguage === 'auto' && styles.selectedLanguage
            ]}
            onPress={() => {
              onSelect('auto');
              setShowLanguageSelector(null);
            }}
          >
            <Text style={styles.languageText}>Auto Detect</Text>
          </TouchableOpacity>
        )}
        {languages.map((language) => (
          <TouchableOpacity
            key={language.code}
            style={[
              styles.languageOption,
              currentLanguage === language.code && styles.selectedLanguage
            ]}
            onPress={() => {
              onSelect(language.code);
              setShowLanguageSelector(null);
            }}
          >
            <Text style={styles.languageText}>
              {language.name} ({language.native_name})
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>
      <TouchableOpacity
        style={styles.closeButton}
        onPress={() => setShowLanguageSelector(null)}
      >
        <Ionicons name="close" size={24} color="#fff" />
      </TouchableOpacity>
    </View>
  );

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.keyboardContainer}
      >
        <ScrollView style={styles.scrollView} keyboardShouldPersistTaps="handled">
          {/* Header */}
          <View style={styles.header}>
            <Ionicons name="language" size={28} color="#4A90E2" />
            <Text style={styles.headerTitle}>AI Translator</Text>
          </View>

          {/* Language Selection Bar */}
          <View style={styles.languageBar}>
            <TouchableOpacity
              style={styles.languageButton}
              onPress={() => setShowLanguageSelector('source')}
            >
              <Text style={styles.languageButtonText}>
                {getLanguageName(sourceLanguage)}
              </Text>
              <Ionicons name="chevron-down" size={16} color="#4A90E2" />
            </TouchableOpacity>

            <TouchableOpacity style={styles.swapButton} onPress={swapLanguages}>
              <Ionicons name="swap-horizontal" size={24} color="#4A90E2" />
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.languageButton}
              onPress={() => setShowLanguageSelector('target')}
            >
              <Text style={styles.languageButtonText}>
                {getLanguageName(targetLanguage)}
              </Text>
              <Ionicons name="chevron-down" size={16} color="#4A90E2" />
            </TouchableOpacity>
          </View>

          {/* Input Section */}
          <View style={styles.translationSection}>
            <View style={styles.inputContainer}>
              <Text style={styles.sectionLabel}>Enter Text</Text>
              <TextInput
                style={styles.textInput}
                multiline
                placeholder="Type text to translate..."
                placeholderTextColor="#999"
                value={inputText}
                onChangeText={setInputText}
                textAlignVertical="top"
              />
              <View style={styles.inputActions}>
                <TouchableOpacity
                  style={styles.clearButton}
                  onPress={() => setInputText('')}
                >
                  <Ionicons name="close-circle" size={20} color="#999" />
                </TouchableOpacity>
              </View>
            </View>

            {/* Translate Button */}
            <TouchableOpacity
              style={[styles.translateButton, isTranslating && styles.translatingButton]}
              onPress={translateText}
              disabled={isTranslating || !inputText.trim()}
            >
              {isTranslating ? (
                <ActivityIndicator color="#fff" size="small" />
              ) : (
                <Ionicons name="arrow-forward" size={20} color="#fff" />
              )}
              <Text style={styles.translateButtonText}>
                {isTranslating ? 'Translating...' : 'Translate'}
              </Text>
            </TouchableOpacity>

            {/* Output Section */}
            {translatedText ? (
              <View style={styles.outputContainer}>
                <Text style={styles.sectionLabel}>Translation</Text>
                <View style={styles.translatedTextContainer}>
                  <Text style={styles.translatedText}>{translatedText}</Text>
                  <TouchableOpacity
                    style={styles.copyButton}
                    onPress={() => {
                      // Copy to clipboard functionality would go here
                      Alert.alert('Copied', 'Translation copied to clipboard');
                    }}
                  >
                    <Ionicons name="copy-outline" size={20} color="#4A90E2" />
                  </TouchableOpacity>
                </View>
              </View>
            ) : null}
          </View>

          {/* Recent Translations */}
          {recentTranslations.length > 0 && (
            <View style={styles.recentSection}>
              <Text style={styles.recentTitle}>Recent Translations</Text>
              {recentTranslations.map((translation, index) => (
                <TouchableOpacity
                  key={translation.id}
                  style={styles.recentItem}
                  onPress={() => {
                    setInputText(translation.original_text);
                    setTranslatedText(translation.translated_text);
                  }}
                >
                  <View style={styles.recentItemContent}>
                    <Text style={styles.recentOriginal} numberOfLines={2}>
                      {translation.original_text}
                    </Text>
                    <Text style={styles.recentTranslated} numberOfLines={2}>
                      {translation.translated_text}
                    </Text>
                    <Text style={styles.recentLanguages}>
                      {getLanguageName(translation.source_language)} → {getLanguageName(translation.target_language)}
                    </Text>
                  </View>
                </TouchableOpacity>
              ))}
            </View>
          )}

          {/* Quick Action Buttons */}
          <View style={styles.quickActions}>
            <TouchableOpacity 
              style={styles.actionButton}
              onPress={() => router.push('/camera')}
            >
              <Ionicons name="camera" size={24} color="#4A90E2" />
              <Text style={styles.actionButtonText}>Camera</Text>
            </TouchableOpacity>
            
            <TouchableOpacity style={styles.actionButton}>
              <Ionicons name="mic" size={24} color="#4A90E2" />
              <Text style={styles.actionButtonText}>Voice</Text>
            </TouchableOpacity>
            
            <TouchableOpacity style={styles.actionButton}>
              <Ionicons name="chatbubbles" size={24} color="#4A90E2" />
              <Text style={styles.actionButtonText}>Conversation</Text>
            </TouchableOpacity>
            
            <TouchableOpacity style={styles.actionButton}>
              <Ionicons name="document-text" size={24} color="#4A90E2" />
              <Text style={styles.actionButtonText}>Document</Text>
            </TouchableOpacity>
          </View>
        </ScrollView>

        {/* Language Selector Modal */}
        {showLanguageSelector && (
          <View style={styles.languageSelectorOverlay}>
            <LanguageSelector
              type={showLanguageSelector}
              currentLanguage={showLanguageSelector === 'source' ? sourceLanguage : targetLanguage}
              onSelect={showLanguageSelector === 'source' ? setSourceLanguage : setTargetLanguage}
            />
          </View>
        )}
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  keyboardContainer: {
    flex: 1,
  },
  scrollView: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 20,
    paddingHorizontal: 16,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e1e8ed',
  },
  headerTitle: {
    fontSize: 22,
    fontWeight: 'bold',
    marginLeft: 12,
    color: '#1a202c',
  },
  languageBar: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 16,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e1e8ed',
  },
  languageButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    paddingHorizontal: 16,
    backgroundColor: '#f7fafc',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#e2e8f0',
  },
  languageButtonText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#4A90E2',
    marginRight: 4,
  },
  swapButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
  },
  translationSection: {
    padding: 16,
    backgroundColor: '#fff',
    marginTop: 8,
  },
  inputContainer: {
    marginBottom: 16,
  },
  sectionLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: '#2d3748',
    marginBottom: 8,
  },
  textInput: {
    borderWidth: 1,
    borderColor: '#e2e8f0',
    borderRadius: 12,
    padding: 16,
    fontSize: 16,
    minHeight: 120,
    backgroundColor: '#fff',
    color: '#2d3748',
  },
  inputActions: {
    position: 'absolute',
    right: 12,
    top: 40,
  },
  clearButton: {
    padding: 4,
  },
  translateButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#4A90E2',
    paddingVertical: 14,
    paddingHorizontal: 24,
    borderRadius: 12,
    marginBottom: 16,
  },
  translatingButton: {
    backgroundColor: '#7bb3f0',
  },
  translateButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 8,
  },
  outputContainer: {
    marginTop: 8,
  },
  translatedTextContainer: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: '#f7fafc',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#e2e8f0',
  },
  translatedText: {
    flex: 1,
    fontSize: 16,
    color: '#2d3748',
    lineHeight: 24,
  },
  copyButton: {
    padding: 4,
    marginLeft: 8,
  },
  recentSection: {
    backgroundColor: '#fff',
    marginTop: 8,
    paddingHorizontal: 16,
    paddingVertical: 16,
  },
  recentTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#2d3748',
    marginBottom: 12,
  },
  recentItem: {
    backgroundColor: '#f7fafc',
    borderRadius: 8,
    padding: 12,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#e2e8f0',
  },
  recentItemContent: {
    gap: 4,
  },
  recentOriginal: {
    fontSize: 14,
    color: '#4a5568',
    fontWeight: '500',
  },
  recentTranslated: {
    fontSize: 14,
    color: '#2d3748',
  },
  recentLanguages: {
    fontSize: 12,
    color: '#718096',
  },
  quickActions: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingHorizontal: 16,
    paddingVertical: 20,
    backgroundColor: '#fff',
    marginTop: 8,
  },
  actionButton: {
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 8,
    backgroundColor: '#f7fafc',
    minWidth: 70,
  },
  actionButtonText: {
    fontSize: 12,
    color: '#4A90E2',
    marginTop: 4,
    fontWeight: '500',
  },
  languageSelectorOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 1000,
  },
  languageSelectorContainer: {
    backgroundColor: '#fff',
    borderRadius: 12,
    width: '90%',
    maxHeight: '70%',
    padding: 16,
  },
  languageList: {
    maxHeight: 400,
  },
  languageOption: {
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 8,
    marginBottom: 4,
  },
  selectedLanguage: {
    backgroundColor: '#4A90E2',
  },
  languageText: {
    fontSize: 16,
    color: '#2d3748',
  },
  closeButton: {
    alignSelf: 'center',
    backgroundColor: '#4A90E2',
    borderRadius: 20,
    padding: 8,
    marginTop: 16,
  },
});