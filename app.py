import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# Configuración inicial de Streamlit
st.set_page_config(page_title="Simulador de ETFs - Allianz Patrimonial", layout="wide")

# --- Sección de Datos Iniciales del Usuario ---
st.title("Simulador de Inversiones - Allianz Patrimonial")

st.header("Registro de Datos Personales")

# Formularios de entrada para datos personales
nombre = st.text_input("Nombre Completo")
celular = st.text_input("Número de Celular")
estado = st.selectbox("Estado", ["Selecciona...", "Aguascalientes", "Baja California", "Chihuahua", "CDMX", "Jalisco", "Nuevo León", "Puebla", "Yucatán", "Otro"])
edad = st.number_input("Edad", min_value=18, max_value=100, step=1)
email = st.text_input("Correo Electrónico")

# Validación para asegurarse de que los datos se hayan ingresado
if st.button("Guardar Datos"):
    if nombre and celular and estado != "Selecciona..." and edad and email:
        st.session_state["user_data"] = {
            "Nombre": nombre,
            "Celular": celular,
            "Estado": estado,
            "Edad": edad,
            "Email": email
        }
        st.success("Datos guardados exitosamente.")
    else:
        st.error("Por favor, completa todos los campos.")

# Solo continuar si los datos están registrados
if "user_data" in st.session_state:
    st.write(f"**Bienvenido, {st.session_state['user_data']['Nombre']}!**")

    # --- Comienza el Simulador de ETFs y Crecimiento Patrimonial ---
    
    # Lista de ETFs populares
    etfs = ["SPY", "QQQ", "EEM", "IVV", "IEMG", "VOO", "VTI", "BND", "GLD"]

    # Sidebar para seleccionar el ETF y el periodo de tiempo
    st.sidebar.header("Selecciona las Opciones")
    selected_etf = st.sidebar.selectbox("Selecciona un ETF", etfs)
    start_date = st.sidebar.date_input("Fecha de inicio", datetime.now() - timedelta(days=365*5))
    end_date = st.sidebar.date_input("Fecha de fin", datetime.now())

    # Función para descargar datos
    @st.cache_data
    def download_data(ticker, start, end):
        try:
            data = yf.download(ticker, start=start, end=end)
            if data.empty:
                st.warning(f"No se encontraron datos para el ticker {ticker}.")
            return data
        except Exception as e:
            st.error(f"Error al descargar datos de {ticker}: {e}")
            st.stop()
            return pd.DataFrame()

    # Descarga de datos
    data = download_data(selected_etf, start_date, end_date)

    # Visualización de datos históricos con indicadores técnicos
    st.header(f"Datos históricos de {selected_etf}")
    # Cálculo de indicadores técnicos
    data['SMA_50'] = data['Close'].rolling(window=50).mean()
    data['SMA_200'] = data['Close'].rolling(window=200).mean()
    data['RSI'] = 100 - (100 / (1 + data['Close'].pct_change().rolling(window=14).mean() / data['Close'].pct_change().rolling(window=14).std()))

    # Gráfico con medias móviles y RSI
    fig, ax = plt.subplots(2, 1, figsize=(12, 8), sharex=True, gridspec_kw={'height_ratios': [3, 1]})
    ax[0].plot(data['Close'], label="Precio de Cierre")
    ax[0].plot(data['SMA_50'], label="SMA 50", linestyle="--")
    ax[0].plot(data['SMA_200'], label="SMA 200", linestyle="--")
    ax[0].set_title(f"{selected_etf} - Precio de Cierre y Medias Móviles")
    ax[0].legend()
    ax[0].set_ylabel("Precio")
    ax[1].plot(data['RSI'], color='purple', label="RSI (14)")
    ax[1].axhline(70, color='red', linestyle="--")
    ax[1].axhline(30, color='green', linestyle="--")
    ax[1].set_title("RSI (Índice de Fuerza Relativa)")
    ax[1].set_ylabel("RSI")
    ax[1].legend()
    st.pyplot(fig)

    # Cálculos de rendimiento y riesgo
    st.header("Rendimiento y Riesgo")
    periodos = {
        "1 mes": 21, "3 meses": 63, "6 meses": 126, "1 año": 252,
        "YTD": (datetime.now() - datetime(datetime.now().year, 1, 1)).days,
        "3 años": 252*3, "5 años": 252*5, "10 años": 252*10
    }

    rendimiento = {}
    volatilidad = {}

    for periodo, days in periodos.items():
        if len(data) >= days:
            data_periodo = data['Close'].tail(days)
            rendimiento[periodo] = round(float((data_periodo.iloc[-1] / data_periodo.iloc[0] - 1) * 100), 2)
            volatilidad[periodo] = round(float(data_periodo.pct_change().std() * np.sqrt(252) * 100), 2)

    # Crear DataFrame para mostrar los resultados de rendimiento y volatilidad
    rend_df = pd.DataFrame({
        "Rendimiento (%)": list(rendimiento.values()),
        "Volatilidad (%)": list(volatilidad.values())
    }, index=rendimiento.keys())
    st.table(rend_df)

    # Simulación de cartera
    st.header("Simulación de Cartera")
    num_assets = st.slider("Número de ETFs en la cartera", 1, len(etfs), 3)
    selected_etfs = st.multiselect("Selecciona los ETFs para la cartera", etfs, etfs[:num_assets])

    # Configuración de la tabla de porcentajes
    if selected_etfs:
        initial_percentage = round(100 / len(selected_etfs), 2)
        percentages = {etf: initial_percentage for etf in selected_etfs}

        # Actualizar los datos en session_state solo si los ETFs seleccionados cambian
        if "selected_etfs" not in st.session_state or st.session_state.selected_etfs != selected_etfs:
            st.session_state.selected_etfs = selected_etfs
            percentages_df = pd.DataFrame(list(percentages.items()), columns=["ETF", "Porcentaje (%)"])
            percentages_df["Porcentaje (%)"] = percentages_df["Porcentaje (%)"].astype(float)
            percentages_df.index += 1
            st.session_state.percentages_df = percentages_df
        else:
            percentages_df = st.session_state.percentages_df

        # Editor de datos interactivo
        edited_percentages_df = st.data_editor(percentages_df, use_container_width=True, key="editor")

        # Comprobación de la suma de porcentajes
        total_percentage = edited_percentages_df["Porcentaje (%)"].sum()
        
        # Mostrar un mensaje y un botón de ajuste si la suma no es 100%
        if total_percentage != 100:
            st.error("La suma debe ser igual al 100%.")
            if st.button("Ajustar porcentajes automáticamente"):
                # Calcular los porcentajes ajustados proporcionalmente
                scale_factor = 100 / total_percentage
                adjusted_percentages = edited_percentages_df["Porcentaje (%)"] * scale_factor
                adjusted_percentages = adjusted_percentages.round(2)
                
                # Ajustar para que sume 100% después del redondeo
                difference = 100.00 - adjusted_percentages.sum()
                adjusted_percentages.iloc[-1] += difference  # Ajusta el último valor para asegurar la suma

                # Actualizar los valores en la tabla principal y guardarlos en session_state
                st.session_state.percentages_df["Porcentaje (%)"] = adjusted_percentages
                st.success("Los porcentajes han sido ajustados y guardados.")
                st.experimental_rerun()  # Refrescar para mostrar los ajustes en la misma tabla
        else:
            st.success("La suma de los porcentajes es igual a 100%.")

        weights = np.array(st.session_state.percentages_df["Porcentaje (%)"]) / 100

        # Descargar datos de los ETFs seleccionados
        cartera_data = pd.DataFrame()
        for ticker in selected_etfs:
            cartera_data[ticker] = download_data(ticker, start_date, end_date)['Close']

        # Verificar que los pesos coincidan con el número de ETFs seleccionados
        if len(weights) != len(cartera_data.columns):
            st.error("El número de pesos no coincide con el número de ETFs seleccionados. Ajusta la selección y los pesos.")
        else:
            # Evolución histórica de la cartera
            cartera_total = (cartera_data * weights).sum(axis=1)
            st.header("Evolución Histórica de la Cartera")
            st.line_chart(cartera_total, use_container_width=True)

            # Calcular rendimientos diarios y matriz de covarianza
            daily_returns = cartera_data.pct_change().dropna()
            cov_matrix = daily_returns.cov() * 252
            expected_return = round(daily_returns.mean().dot(weights) * 252 * 100, 2)  # Rendimiento esperado en porcentaje
            portfolio_volatility = round(np.sqrt(weights.T.dot(cov_matrix).dot(weights)) * 100, 2)

            st.write("*Rendimiento Esperado de la Cartera (%):*", expected_return)
            st.write("*Riesgo de la Cartera (Volatilidad %):*", portfolio_volatility)

            # Simulación de Ahorro e Inversión Personalizada
            st.header("Simulador de Ahorro e Inversión Personalizada")

            # Usar el "Rendimiento Esperado de la Cartera" como tasa para el simulador
            rendimiento_anual = expected_return / 100  # Convertir a decimal

            # Entradas del simulador
            aportacion_inicial = st.number_input("Aportación inicial", min_value=0, value=1000, step=100)
            aportacion_periodica = st.number_input("Aportación periódica", min_value=0, value=100, step=10)
            frecuencia_aportacion = st.selectbox("Frecuencia de aportaciones", ["Mensual", "Semestral", "Anual"])
            horizonte_inversion = st.selectbox("Horizonte de inversión (años)", [5, 10, 15, 20])

            # Convertir frecuencia a número de aportaciones por año
            frecuencias = {"Mensual": 12, "Semestral": 2, "Anual": 1}
            num_aportaciones_anuales = frecuencias[frecuencia_aportacion]

            # Simulación de crecimiento de inversión con rendimiento y sin rendimiento
            patrimonio_inversion = [aportacion_inicial]  # Lista para el crecimiento con rendimiento
            patrimonio_ahorro = [aportacion_inicial]     # Lista para el ahorro sin rendimiento

            for year in range(1, horizonte_inversion + 1):
                # Calcular el crecimiento anual con aportaciones periódicas para ambas líneas
                for _ in range(num_aportaciones_anuales):
                    # Inversión con rendimiento
                    patrimonio_inversion[-1] += aportacion_periodica
                    patrimonio_inversion[-1] *= (1 + rendimiento_anual / num_aportaciones_anuales)
                    
                    # Ahorro sin rendimiento (solo sumando las aportaciones)
                    patrimonio_ahorro[-1] += aportacion_periodica
                
                # Añadir el valor de fin de año a ambas listas
                patrimonio_inversion.append(patrimonio_inversion[-1])
                patrimonio_ahorro.append(patrimonio_ahorro[-1])

            # Visualización de crecimiento de inversión
            st.subheader("Evolución del Crecimiento de la Inversión vs. Ahorro sin Rendimiento")
            plt.figure(figsize=(10, 6))

            # Línea de inversión con rendimiento
            plt.plot(range(horizonte_inversion + 1), patrimonio_inversion, marker='o', linestyle='-', label="Inversión con Rendimiento")

            # Línea de ahorro sin rendimiento
            plt.plot(range(horizonte_inversion + 1), patrimonio_ahorro, marker='o', linestyle='--', color="orange", label="Ahorro sin Rendimiento")

            plt.xlabel("Años")
            plt.ylabel("Valor de la Inversión")
            plt.title("Comparación: Inversión con Rendimiento vs Ahorro sin Rendimiento")
            plt.legend()
            plt.grid(True)
            st.pyplot(plt)

            # Mostrar el valor final de la inversión con rendimiento centrado y resaltado
            valor_final_inversion = patrimonio_inversion[-1]
            st.markdown(
                f"<h3 style='text-align: center; color: #4CAF50; font-size: 28px;'>"
                f"Valor final estimado de la inversión después de {horizonte_inversion} años: ${valor_final_inversion:,.2f}"
                f"</h3>",
                unsafe_allow_html=True
            )

            # Mostrar el valor final de ahorro sin rendimiento centrado y resaltado
            valor_final_ahorro = patrimonio_ahorro[-1]
            st.markdown(
                f"<h3 style='text-align: center; color: #FF5722; font-size: 28px;'>"
                f"Valor acumulado sin rendimiento después de {horizonte_inversion} años: ${valor_final_ahorro:,.2f}"
                f"</h3>",
                unsafe_allow_html=True
            )

    st.write("Esta es una aplicación interactiva creada para simular ETFs y carteras patrimoniales.")
