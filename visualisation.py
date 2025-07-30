import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- CONFIGURATION & FONCTIONS UTILITAIRES (Inchangé) ---
PLOTLY_CONFIG = {
    'template': 'plotly_white',
    'layout': {
        'plot_bgcolor': 'rgba(0,0,0,0)',
        'paper_bgcolor': 'rgba(0,0,0,0)',
        'font': {'family': 'sans-serif', 'color': '#333'},
        'title': {'x': 0.5, 'font': {'size': 18}},
    }
}

def get_numeric_columns(df):
    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
    return [col for col in numeric_cols if not col.endswith('_outlier')]

def get_categorical_columns(df):
    return df.select_dtypes(include=['object', 'category']).columns.tolist()

# --- NOUVELLE FONCTION POUR LE DASHBOARD KPI ---

def create_kpi_dashboard(df, numeric_cols, all_cols):
    """
    Crée un dashboard de KPIs interactif où l'utilisateur définit les métriques.
    Aide à suivre la performance de l'activité représentée par les données.
    """
    st.markdown("### ⭐ Indicateurs Clés de Performance (KPIs)")
    st.info(
        "Définissez ici vos propres KPIs ! Choisissez les colonnes qui représentent vos métriques principales, "
        "vos dimensions d'analyse et l'axe temporel pour visualiser la performance."
    )

    # Création d'un formulaire pour les sélections
    with st.form("kpi_form"):
        st.markdown("**Configurez vos indicateurs :**")
        col1, col2, col3 = st.columns(3)
        with col1:
            # Colonne pour les calculs principaux (somme, moyenne)
            metric_col = st.selectbox("Choisissez votre métrique principale (numérique) :", [None] + numeric_cols)
        with col2:
            # Colonne pour l'analyse temporelle
            date_col = st.selectbox("Choisissez votre colonne de date :", [None] + all_cols)
        with col3:
            # Colonne pour compter des entités uniques (clients, produits...)
            dimension_col = st.selectbox("Choisissez une dimension à compter :", [None] + all_cols)
        
        submitted = st.form_submit_button("Générer les KPIs")

    if not submitted:
        st.write("Veuillez configurer et soumettre le formulaire pour voir vos KPIs.")
        return

    st.divider()
    
    # Affichage des KPIs dans des colonnes
    kpi_cols = st.columns(3)
    
    # KPI 1: Total et Moyenne de la métrique
    if metric_col:
        total_metric = df[metric_col].sum()
        mean_metric = df[metric_col].mean()
        kpi_cols[0].metric(f"Total de {metric_col}", f"{total_metric:,.2f}")
        kpi_cols[0].metric(f"Moyenne de {metric_col}", f"{mean_metric:,.2f}")

    # KPI 2: Comptage d'éléments uniques
    if dimension_col:
        unique_count = df[dimension_col].nunique()
        kpi_cols[1].metric(f"Nombre de '{dimension_col}' uniques", f"{unique_count:,}")

    # KPI 3 & Graphique: Analyse temporelle
    if date_col and metric_col:
        try:
            # Copie pour éviter SettingWithCopyWarning
            temp_df = df[[date_col, metric_col]].copy()
            # Conversion de la colonne date en datetime
            temp_df[date_col] = pd.to_datetime(temp_df[date_col])
            temp_df = temp_df.sort_values(by=date_col).set_index(date_col)
            
            # Calcul de tendance (comparaison 2e moitié vs 1re moitié)
            mid_point = len(temp_df) // 2
            first_half_sum = temp_df[metric_col].iloc[:mid_point].sum()
            second_half_sum = temp_df[metric_col].iloc[mid_point:].sum()
            
            delta = 0
            if first_half_sum > 0:
                delta = ((second_half_sum - first_half_sum) / first_half_sum) * 100

            kpi_cols[2].metric(
                f"Tendance de {metric_col}",
                f"{second_half_sum:,.2f} (2e moitié)",
                f"{delta:.2f}% vs 1re moitié"
            )

            # Graphique d'évolution temporelle
            st.markdown(f"#### Évolution de **{metric_col}** dans le temps")
            resampled_df = temp_df.resample('D').sum().reset_index() # Agréger par jour
            
            fig_time = px.area(
                resampled_df,
                x=date_col,
                y=metric_col,
                title=f"Performance de {metric_col} au fil du temps",
                labels={'x': 'Date', 'y': metric_col}
            )
            fig_time.update_layout(**PLOTLY_CONFIG['layout'])
            st.plotly_chart(fig_time, use_container_width=True)

        except Exception as e:
            st.error(f"Erreur lors de l'analyse temporelle : {e}. Assurez-vous que la colonne '{date_col}' est bien un format de date valide.")
            
# --- FONCTIONS DE VISUALISATION (Adaptées) ---

def create_dashboard_overview(df):
    st.markdown("### 🔎 Vue d'Ensemble du Dataset")
    st.write("Cette section vous donne un résumé de haut niveau de vos données. Idéal pour un premier diagnostic.")

    # Section renommée : "Informations sur le Dataset"
    st.markdown("##### Informations sur le Dataset")
    completeness = (1 - df.isnull().sum().sum() / df.size) * 100
    duplicates = df.duplicated().sum()
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📝 Lignes", f"{len(df):,}")
    col2.metric("📏 Colonnes", len(df.columns))
    col3.metric("✅ Complétude", f"{completeness:.1f}%", help="Pourcentage de cellules non-vides.")
    col4.metric("🔗 Doublons", f"{duplicates:,}", help="Nombre de lignes entièrement identiques.")

    st.divider()
    # Le reste de la fonction est inchangé...
    col1, col2 = st.columns([1, 2])
    with col1:
        # ...
        st.markdown("##### Répartition des Types de Données")
        type_counts = df.dtypes.astype(str).value_counts()
        fig_types = px.pie(
            values=type_counts.values,
            names=type_counts.index,
            title="Types de variables",
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig_types.update_layout(**PLOTLY_CONFIG['layout'], showlegend=False)
        fig_types.update_traces(textinfo='percent+label', textposition='inside')
        st.plotly_chart(fig_types, use_container_width=True)
    with col2:
        # ...
        st.markdown("##### Analyse des Valeurs Manquantes")
        missing_data = df.isnull().sum()
        missing_data = missing_data[missing_data > 0].sort_values(ascending=False)
        
        if not missing_data.empty:
            fig_missing = px.bar(
                x=missing_data.index,
                y=(missing_data.values / len(df)) * 100,
                title="Taux de Valeurs Manquantes (> 0%)",
                labels={'x': 'Colonne', 'y': '% Manquant'},
                color=missing_data.values,
                color_continuous_scale='Reds'
            )
            fig_missing.update_layout(**PLOTLY_CONFIG['layout'])
            st.plotly_chart(fig_missing, use_container_width=True)
        else:
            st.success("✅ Félicitations ! Aucune valeur manquante détectée.")
    with st.expander("💡 Insights et Recommandations"):
        if completeness < 85:
            st.warning("⚠️ **Action Requise :** La complétude est faible. Envisagez des techniques d'imputation (moyenne, médiane) ou de suppression des lignes/colonnes avec trop de valeurs manquantes.")
        if duplicates > 0:
            st.info(f"ℹ️ **Information :** {duplicates} doublons trouvés. Pensez à les supprimer pour éviter les biais dans vos analyses.")
        st.success("🎯 **Prochaine Étape :** Explorez l'onglet 'Analyse Univariée' pour comprendre la distribution de chaque variable individuellement.")


def create_univariate_analysis(df, numeric_cols, cat_cols):
    # Cette fonction reste inchangée
    st.markdown("### 📊 Analyse Univariée (une variable à la fois)")
    st.write("Explorez ici chaque variable pour comprendre sa distribution, sa tendance centrale et sa dispersion.")
    st.markdown("#### Distribution des Variables Numériques")
    if not numeric_cols:
        st.warning("Aucune variable numérique détectée.")
    else:
        selected_numeric = st.selectbox("Choisissez une variable numérique :", numeric_cols)
        st.info("Regardez la forme de l'histogramme pour comprendre la distribution et le box plot pour identifier facilement la médiane et les potentiels outliers (points).")
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.8, 0.2])
        fig.add_trace(go.Histogram(x=df[selected_numeric], name='Histogramme', marker_color='#2E86AB'), row=1, col=1)
        fig.add_trace(go.Box(x=df[selected_numeric], name='Box Plot', marker_color='#A23B72'), row=2, col=1)
        fig.update_layout(title_text=f"Distribution de {selected_numeric}",**PLOTLY_CONFIG['layout'],showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df[selected_numeric].describe().to_frame().T, use_container_width=True)
    st.divider()
    st.markdown("#### Distribution des Variables Catégorielles")
    if not cat_cols:
        st.warning("Aucune variable catégorielle détectée.")
    else:
        selected_cat = st.selectbox("Choisissez une variable catégorielle :", cat_cols)
        st.info("Ce graphique montre la fréquence de chaque catégorie. Idéal pour voir quelles sont les valeurs les plus communes.")
        value_counts = df[selected_cat].value_counts().head(20)
        fig_bar = px.bar(x=value_counts.index,y=value_counts.values,title=f"Top 20 des catégories pour {selected_cat}",labels={'x': selected_cat, 'y': 'Fréquence'},color=value_counts.values,color_continuous_scale='Cividis')
        fig_bar.update_layout(**PLOTLY_CONFIG['layout'])
        st.plotly_chart(fig_bar, use_container_width=True)

def create_bivariate_analysis(df, numeric_cols, cat_cols):
    # Cette fonction reste inchangée
    st.markdown("### 🔗 Analyse Bivariée (relations entre deux variables)")
    st.write("Comment vos variables interagissent-elles ? C'est ici que vous pouvez découvrir des relations cachées.")
    analysis_type = st.radio("Quel type d'analyse souhaitez-vous effectuer ?",("Numérique vs Numérique (Corrélation)", "Numérique vs Catégorielle (Comparaison)"),horizontal=True)
    if analysis_type == "Numérique vs Numérique (Corrélation)":
        if len(numeric_cols) < 2:
            st.warning("Il faut au moins deux variables numériques pour cette analyse.")
            return
        st.markdown("#### Matrice de Corrélation")
        st.info("Cette carte de chaleur montre la force de la relation linéaire entre les variables. Bleu = corrélation positive, Rouge = corrélation négative. Proche de 1 ou -1 indique une forte relation.")
        corr_matrix = df[numeric_cols].corr()
        fig_corr = px.imshow(corr_matrix, text_auto=".2f", aspect="auto",color_continuous_scale='RdBu_r', range_color=[-1, 1],title="Matrice de Corrélation")
        fig_corr.update_layout(**PLOTLY_CONFIG['layout'])
        st.plotly_chart(fig_corr, use_container_width=True)
        st.markdown("#### Exploration de la Relation")
        col1, col2, col3 = st.columns(3)
        x_var = col1.selectbox("Variable X :", numeric_cols, key="scatter_x")
        y_var = col2.selectbox("Variable Y :", numeric_cols, index=min(1, len(numeric_cols)-1), key="scatter_y")
        color_var = col3.selectbox("Colorer par (optionnel) :", [None] + cat_cols, key="scatter_color")
        if x_var != y_var:
            fig_scatter = px.scatter(df, x=x_var, y=y_var, color=color_var,trendline="ols",title=f"Relation entre {x_var} et {y_var}",color_continuous_scale='Viridis')
            fig_scatter.update_layout(**PLOTLY_CONFIG['layout'])
            st.plotly_chart(fig_scatter, use_container_width=True)
            correlation = df[x_var].corr(df[y_var])
            st.metric("Coefficient de corrélation (Pearson)", f"{correlation:.3f}")
    elif analysis_type == "Numérique vs Catégorielle (Comparaison)":
        if not numeric_cols or not cat_cols:
            st.warning("Il faut au moins une variable numérique et une catégorielle pour cette analyse.")
            return
        st.markdown("#### Comparaison de groupes")
        st.info("Utilisez ces graphiques pour comparer une mesure numérique à travers différentes catégories. Cherchez des différences significatives dans les moyennes (ligne dans la boîte) ou les distributions.")
        col1, col2 = st.columns(2)
        numeric_var = col1.selectbox("Variable numérique à comparer :", numeric_cols, key="comp_num")
        cat_var = col2.selectbox("Variable catégorielle pour grouper :", cat_cols, key="comp_cat")
        if numeric_var and cat_var:
            fig_box = px.box(df, x=cat_var, y=numeric_var, color=cat_var,title=f"Distribution de {numeric_var} par {cat_var}",color_discrete_sequence=px.colors.qualitative.Prism)
            fig_box.update_layout(**PLOTLY_CONFIG['layout'])
            st.plotly_chart(fig_box, use_container_width=True)
            st.markdown("##### Statistiques par groupe")
            st.dataframe(df.groupby(cat_var)[numeric_var].describe(), use_container_width=True)

# --- FONCTION PRINCIPALE DE L'APPLICATION (Adaptée) ---

def create_visualizations(df):
    """Point d'entrée principal pour générer toutes les visualisations."""
    if df is None or df.empty:
        st.warning("Veuillez charger un fichier de données pour commencer l'analyse.")
        return

    st.header("Dashboard d'Analyse Exploratoire des Données", divider='rainbow')

    for col in df.select_dtypes(include='object').columns:
        if df[col].nunique() / len(df) < 0.1 and df[col].nunique() < 50:
            df[col] = df[col].astype('category')
            
    numeric_columns = get_numeric_columns(df)
    categorical_columns = get_categorical_columns(df)
    all_columns = df.columns.tolist() # Pour le sélecteur de date

    # Nouvelle structure avec l'onglet KPI
    tab1, tab2, tab3, tab4 = st.tabs(["⭐ KPIs", "🔎 Vue d'Ensemble", "📊 Analyse Univariée", "🔗 Analyse Bivariée"])

    with tab1:
        create_kpi_dashboard(df, numeric_columns, all_columns)

    with tab2:
        create_dashboard_overview(df)
    
    with tab3:
        create_univariate_analysis(df, numeric_columns, categorical_columns)
        
    with tab4:
        create_bivariate_analysis(df, numeric_columns, categorical_columns)