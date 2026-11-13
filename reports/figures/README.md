# Visualisations et Figures du Modèle ANAPEC

Ce dossier regroupe les visualisations générées lors de l'évaluation du moteur de matching IA :

1. **`f1_vs_threshold.svg`** :  
   Courbe d'optimisation du seuil de similarité cosinus. Présente l'évolution conjointe de la Précision, du Rappel et du F1-Score sur une plage de seuils [0.20, 0.80]. Met en évidence le pic optimal à **`seuil = 0.26`** atteignant un F1-Score maximal de **78.82 %**.

2. **`confusion_matrix.svg`** :  
   Matrice de confusion sur le jeu de test indépendant constitué de 12 124 paires (6 062 paires positives issues des relations essentielles ESCO et 6 062 paires négatives générées par échantillonnage aléatoire hors domaine).  
   - **Vrais Positifs (TP)** : 4 966  
   - **Vrais Négatifs (TN)** : 4 445  
   - **Faux Positifs (FP)** : 1 617  
   - **Faux Négatifs (FN)** : 1 096  
   - **Exactitude globale** : 77.63 %  
   - **Précision** : 75.45 %  
   - **Rappel** : 81.92 %

