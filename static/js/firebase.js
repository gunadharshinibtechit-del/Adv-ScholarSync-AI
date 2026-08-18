import { initializeApp } from "https://www.gstatic.com/firebasejs/11.6.1/firebase-app.js";

import {
    getAuth,
    signInWithEmailAndPassword,
    createUserWithEmailAndPassword,
    onAuthStateChanged,
    signOut
} from "https://www.gstatic.com/firebasejs/11.6.1/firebase-auth.js";

import {
    getFirestore
} from "https://www.gstatic.com/firebasejs/11.6.1/firebase-firestore.js";


// ==========================================
// FIREBASE CONFIG
// ==========================================

const firebaseConfig = {

    apiKey: "AIzaSyD284UrPXVydNe0qk6xMjGqFaq7BDUVzwI",

    authDomain: "chatbot-834c3.firebaseapp.com",

    projectId: "chatbot-834c3",

    storageBucket: "chatbot-834c3.firebasestorage.app",

    messagingSenderId: "422487927818",

    appId: "1:422487927818:web:42fd0743878e7b0e8483f3"
};


// ==========================================
// INITIALIZE FIREBASE
// ==========================================

const app = initializeApp(firebaseConfig);


// ==========================================
// FIREBASE AUTH
// ==========================================

const auth = getAuth(app);


// ==========================================
// FIRESTORE
// ==========================================

const db = getFirestore(app);


// ==========================================
// EXPORT
// ==========================================

export {
    app,
    auth,
    db,
    signInWithEmailAndPassword,
    createUserWithEmailAndPassword,
    onAuthStateChanged,
    signOut
};