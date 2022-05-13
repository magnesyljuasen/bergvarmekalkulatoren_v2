import streamlit as st
import pandas as pd
import numpy as np
import mpu
import math
import pydeck as pdk
import matplotlib.pyplot as plt 
plt.style.use('classic')
from PIL import Image
from streamlit_folium import folium_static
from geopy.geocoders import Nominatim
from streamlit_lottie import st_lottie
import requests
from matplotlib.backends.backend_agg import RendererAgg
import altair as alt

def load_lottie(url: str):
    r = requests.get(url)
    if r.status_code!= 200:
        return None
    return r.json()

def hour_to_month (hourly_array):
    monthly_array = []
    summert = 0
    for i in range(0, len(hourly_array)):
        verdi = hourly_array[i]
        if np.isnan(verdi):
            verdi = 0
        summert = verdi + summert
        if i == 744 or i == 1416 or i == 2160 or i == 2880 \
                or i == 3624 or i == 4344 or i == 5088 or i == 5832 \
                or i == 6552 or i == 7296 or i == 8016 or i == 8759:
            monthly_array.append(int(summert))
            summert = 0
    return monthly_array


class Veienvidere:
    def __init__(self):
        url1 = "https://www.varmepumpeinfo.no/forhandlersok"
        st.header("Få et uforpliktende tilbud på bergvarme [her](%s)" % url1)

        url2 = "https://www.enova.no/privat/alle-energitiltak/varmepumper/vaske-til-vann-varmepumpe-/"
        st.header("Søk ENOVA støtte [her](%s)" % url2)

        url3 = "https://www.varmepumpeinfo.no/energikilder-for-varmepumper/bergvarme"
        st.header("Lær mer om bergvarme [her](%s)" % url3)

        url4 = "https://www.asplanviak.no/tjenester/grunnvarme/"
        st.header("Rådgivningstjenester for større anlegg [her](%s)" % url4)

        image = Image.open('Bilder/AsplanViak_illustrasjoner-02.png')
        st.image(image)




class Co2:
    def __init__(self):
        pass

    def beregning(self, energibehov_hourly, kompressor_energi_y):
        co2_per_kwh = 0.17 / 1000
        co2_el_yearly = round(np.sum(energibehov_hourly) * co2_per_kwh)
        co2_gv_yearly = kompressor_energi_y * co2_per_kwh

        x_axis = np.array(range(1, 26))

        co2_el_ligning = co2_el_yearly * x_axis
        co2_gv_ligning = co2_gv_yearly * x_axis

        data = pd.DataFrame({'År' : x_axis, 'Bergvarme' : co2_gv_ligning, 'Elektrisk oppvarming' : co2_el_ligning})
        c = alt.Chart(data).transform_fold(
            ['Bergvarme', 'Elektrisk oppvarming'],
            as_=['Forklaring', 'CO2 utslipp (tonn)']).mark_line().encode(
            x=alt.X('År:N', sort=x_axis),
            y='CO2 utslipp (tonn):Q',
            color=alt.Color('Forklaring:N', scale=alt.Scale(domain=['Bergvarme', 'Elektrisk oppvarming'], 
            range=['#48a23f', '#880808']), legend=alt.Legend(orient='top', direction='vertical', title=None)))
        st.altair_chart(c, use_container_width=True)


        #Lock
        #lock = RendererAgg.lock
        #with lock:
            #plt.rcParams['axes.facecolor'] = '#FFFFFF'
            #plt.rcParams['savefig.facecolor'] = '#F6F8F1'

            #elektrisk_oppvarming_label = 'Elektrisk oppvarming: ' + str(round (co2_el_ligning[-1])) + ' tonn'
            #bergvarme_label = 'Bergvarme: ' + str(round (co2_gv_ligning[-1])) + ' tonn'
            #plt.plot(x_axis, co2_el_ligning, label='Elektrisk oppvarming', color = '#880808')
            #plt.plot(x_axis, co2_gv_ligning, label='Bergvarme', color = '#48a23f')

            #plt.legend(loc='best')
            #plt.grid()
            #plt.xlabel('År')
            #plt.ylabel("CO2 utslipp [tonn]")
            #st.pyplot(plt)
            #plt.close()

        res_column_1, res_column_2, res_column_3 = st.columns(3)
        with res_column_1:
            st.metric('CO2 Bergvarme', str(round (co2_gv_ligning[-1])) + ' tonn')
        with res_column_2:
            st.metric('CO2 Elektrisk oppvarming', str(round (co2_el_ligning[-1])) + ' tonn')
        with res_column_3:
            st.metric('CO2 Besparelse', str(round (co2_el_ligning[-1] - co2_gv_ligning[-1])) + ' tonn')




class Kostnader:
    def __init__(self, dybde_til_fjell, varmepumpe_storrelse, antall_meter, kompressor, energibehov, el_pris):
        self.dybde_til_fjell = dybde_til_fjell
        self.varmepumpe_storrelse = varmepumpe_storrelse
        self.antall_meter = antall_meter
        self.kompressor_gv_hourly = kompressor
        self.energibehov_hourly = energibehov
        self.el_pris = el_pris

    def oppdater_dybde_til_fjell(self):
        self.dybde_til_fjell = st.number_input ('Oppgi dybde til fjell [m]', value = self.dybde_til_fjell, min_value = 0, max_value = 50)
        st.caption (""" Dybde til fjell [m] er en viktig parameter for å beregne kostnaden for
         brønnboring. Foreslått dybde til fjell er basert på målt dybde til fjell i nærmeste energibrønn. 
         Dybde til fjell har stor lokal variasjon og bør sjekkes mot Nasjonal database for grunnundersøkelser (NADAG).
         Lenke: https://geo.ngu.no/kart/nadag-avansert/ """)

    def investeringskostnad (self):
        if self.varmepumpe_storrelse <= 6:  # 6 kW
            varmepumpe_pris = 91066 + 50000
        elif self.varmepumpe_storrelse >= 6 and self.varmepumpe_storrelse < 8:  # 8 kW
            varmepumpe_pris = 96885 + 50000
        elif self.varmepumpe_storrelse >= 8:  # 10 kW
            varmepumpe_pris = 126853 + 50000

        etablering_pris = 3500
        odex_sko_pris = 575
        bunnlodd_pris = 1000
        lokk_pris = 700

        odex_i_losmasser_pris = 500  # per meter
        fjellboring_pris = 150  # per meter
        kollektor_pris = 55  # per meter

        return round (int(varmepumpe_pris + etablering_pris + odex_sko_pris + bunnlodd_pris + lokk_pris
                                  + self.dybde_til_fjell * (odex_i_losmasser_pris)
                                  + (self.antall_meter - self.dybde_til_fjell) * fjellboring_pris
                                  + (self.antall_meter - 1) * kollektor_pris), -2)

    def plot_investeringskostnad(self):
        x_axis = np.array(range(1, 26))
        el_ligning = self.kostnad_el_yearly * x_axis
        gv_ligning = self.kostnad_gv_yearly * x_axis + self.investeringskostnad()
        self.nedbetalingstid = round(self.investeringskostnad() / (self.kostnad_el_yearly - self.kostnad_gv_yearly))
        self.besparelse = round (el_ligning [-1] - gv_ligning [-1], -2)

        data = pd.DataFrame({'År' : x_axis, 'Bergvarme' : gv_ligning, 'Elektrisk oppvarming' : el_ligning})
        c = alt.Chart(data).transform_fold(
            ['Bergvarme', 'Elektrisk oppvarming'],
            as_=['Forklaring', 'CO2 utslipp (tonn)']).mark_line().encode(
            x=alt.X('År:N', sort=x_axis),
            y='CO2 utslipp (tonn):Q',
            color=alt.Color('Forklaring:N', scale=alt.Scale(domain=['Bergvarme', 'Elektrisk oppvarming'], 
            range=['#48a23f', '#880808']), legend=alt.Legend(orient='top', direction='vertical', title=None)))
        st.altair_chart(c, use_container_width=True)

        #Lock
        #lock = RendererAgg.lock
        #with lock:
            #plt.plot(x_axis, el_ligning, label='Elektrisk oppvarming', color = '#880808')
            #plt.plot(x_axis, gv_ligning, label='Bergvarme', color = '#48a23f')
            #plt.rcParams['axes.facecolor'] = '#FFFFFF'
            #plt.rcParams['savefig.facecolor'] = '#F6F8F1'
            #plt.legend(loc='best')
            #plt.grid()
            #plt.xlim(0,25)
            #plt.xlabel('År')
            #plt.ylabel("Kostnader [kroner]")
            #st.pyplot(plt)
            #plt.close()

        res_column_1, res_column_2, res_column_3 = st.columns(3)
        with res_column_1:
            st.metric('Estimert investeringskostnad', str(self.investeringskostnad()) + ' kr')
        with res_column_2:
            st.metric('Nedbetalingstid', str(self.nedbetalingstid) + ' år')
        with res_column_3:
            st.metric('Gevinst etter 25 år', str(self.besparelse) + ' kr')

    def monthly_costs (self):
        kostnad_el_hourly = self.energibehov_hourly * self.el_pris
        kostnad_gv_hourly = self.kompressor_gv_hourly * self.el_pris

        kostnad_el_monthly = hour_to_month(kostnad_el_hourly)
        kostnad_gv_monthly = hour_to_month(kostnad_gv_hourly)

        kostnad_el_yearly = int(np.nansum(kostnad_el_monthly))
        kostnad_gv_yearly = int(np.nansum(kostnad_gv_monthly))
        self.kostnad_el_yearly = kostnad_el_yearly
        self.kostnad_gv_yearly = kostnad_gv_yearly

        st.write('Fra første dag bergvarmeanlegget settes i gang vil dine månedlige utgifter fordele seg '
                 'som i søylediagrammet under.')
                 
        months = ['jan', 'feb', 'mar', 'apr', 'mai', 'jun', 'jul', 'aug', 'sep', 'okt', 'nov', 'des']
        #---
        wide_form = pd.DataFrame({
            'Måneder' : months,
            'Bergvarme' : kostnad_gv_monthly, 
            'Elektrisk oppvarming' : kostnad_el_monthly
            })

        c1 = alt.Chart(wide_form).transform_fold(
            ['Bergvarme', 'Elektrisk oppvarming'],
            as_=['key', 'Kostnader (kr)']).mark_bar(opacity=1).encode(
                x=alt.X('Måneder:N', sort=months, title=None),
                y=alt.Y('Kostnader (kr):Q',stack=None),
                color=alt.Color('key:N', scale=alt.Scale(domain=['Bergvarme'], 
                range=['#48a23f']), legend=alt.Legend(orient='top', direction='vertical', title=None)
                ))

        c2 = alt.Chart(wide_form).transform_fold(
            ['Bergvarme', 'Elektrisk oppvarming'],
            as_=['key', 'Kostnader (kr)']).mark_bar(opacity=1).encode(
                x=alt.X('Måneder:N', sort=months, title=None),
                y=alt.Y('Kostnader (kr):Q',stack=None, title=None),
                color=alt.Color('key:N', scale=alt.Scale(domain=['Elektrisk oppvarming'], 
                range=['#880808']), legend=alt.Legend(orient='top', direction='vertical', title=None)
                ))
        col1, col2 = st.columns(2)
        with col1:
            st.altair_chart(c1, use_container_width=True)  
        with col2:
            st.altair_chart(c2, use_container_width=True)  
        




                #alt.Color('key:N', scale=alt.Scale(domain=['Bergvarme', 'Elektrisk oppvarming'], 
                #range=['#48a23f', '#880808']), legend=alt.Legend(orient='top', direction='vertical', title=None)),
                #column=alt.Column('Måneder:N', sort=months, header=alt.Header(title=None))            
                #).resolve_scale(x='shared').configure_view(stroke='transparent')

        #c = alt.Chart(wide_form).transform_fold(
        #    ['Bergvarme', 'Elektrisk oppvarming'],
        #    as_=['key', 'Kostnader (kr)']).mark_bar().encode(
        #        x=alt.X('Måneder:N', sort=months),
        #        #x=alt.X('key:N', axis=None),
        #        y='Kostnader (kr):Q',
        #        color=alt.Color('key:N', scale=alt.Scale(domain=['Bergvarme', 'Elektrisk oppvarming'], 
        #        range=['#48a23f', '#880808']), legend=alt.Legend(orient='top', direction='vertical', title=None)),
        #        #column=alt.Column('Måneder:N', sort=months, header=alt.Header(title=None))            
        #        ).resolve_scale(x='shared').configure_view(stroke='transparent')
            

        #Lock
        #lock = RendererAgg.lock
        #with lock:
        #    plt.bar(x_axis - 0.2, kostnad_el_monthly, 0.4, label='Elektrisk oppvarming', color = '#880808')
        #    plt.bar(x_axis + 0.2, kostnad_gv_monthly, 0.4, label='Bergvarme', color = '#48a23f')
        #    plt.rcParams['axes.facecolor'] = '#FFFFFF'
        #    plt.rcParams['savefig.facecolor'] = '#F6F8F1'
        #    plt.xticks(x_axis, months)
        #    plt.legend(loc='best')
        #    plt.grid()
        #    plt.ylabel("Kostnader [kr]")
        #    st.pyplot(plt)
        #    plt.close()

        cost_column_1, cost_column_2, cost_column_3 = st.columns(3)
        with cost_column_1:
            st.metric(label="Bergvarme", value=(str(round(kostnad_gv_yearly, -2)) + " kr"))
        with cost_column_2:
            st.metric(label="Drift - Elektrisk oppvarming", value=(str(round(kostnad_el_yearly, -2)) + " kr"))
        with cost_column_3:
            st.metric('Årlig besparelse', str(round (kostnad_el_yearly - kostnad_gv_yearly, -2)) + ' kr')

    def gronne_laan (self):
        x_axis = np.array(range(1, 26))
        x_axis_laan = np.array(range(1, 27))
        c1, c2 = st.columns(2)
        with c1:
            nedbetalingstid = st.number_input('Nedbetalingstid energilån [år]', value=10, min_value=1, max_value=25,step=1)
        with c2:
            effektiv_rente = st.number_input('Effektiv rente [%]', value=2.44, min_value=1.00, max_value=10.00) / 100

        monthly_antall = nedbetalingstid * 12
        monthly_rente = effektiv_rente / 12
        termin_monthly = self.investeringskostnad() / ((1 - (1 / (1 + monthly_rente) ** monthly_antall)) / monthly_rente)
        termin_yearly = termin_monthly * 12

        el_ligning = self.kostnad_el_yearly * x_axis
        gv_ligning_1 = []
        gv_ligning_2 = []

        j = -1
        for i in range(1, len(x_axis_laan)):
            if i <= nedbetalingstid:
                verdi = (self.kostnad_gv_yearly + termin_yearly) * i
                gv_ligning_1.append(verdi)
            if i >= nedbetalingstid:
                j += 1
                x_axis_laan[i] = i
                gv_ligning_2.append(self.kostnad_gv_yearly * j + verdi)

        gv_ligning = gv_ligning_1 + gv_ligning_2

        #Lock
        lock = RendererAgg.lock
        with lock:
            plt.plot(x_axis, el_ligning, label='Elektrisk oppvarming', color = '#880808')
            plt.plot(x_axis_laan, gv_ligning, label='Bergvarme m/ grønt lån', color = '#48a23f')
            plt.rcParams['axes.facecolor'] = '#FFFFFF'
            plt.rcParams['savefig.facecolor'] = '#F6F8F1'
            plt.legend(loc='best')
            plt.grid()
            plt.xlim(0,25)
            plt.xlabel('År')
            plt.ylabel("Kostnader [kroner]")
            st.pyplot(plt)
            plt.close()




class Strompriser ():
    def __init__(self):
        pass

    def input (self):
        self.year = st.selectbox('Hvilken årlig strømpris skal ligge til grunn?',('2021', '2020', '2019', '2018', 'Gjennomsnitt av de siste 4 år'))
        self.region = st.selectbox('Hvilken strømregion skal strømprisen baseres på?',('Sørøst-Norge', 'Sørvest-Norge', 'Midt-Norge', 'Nord-Norge', 'Vest-Norge'))

    @st.cache
    def el_spot_pris (self):
        if self.year == '2018':
            el_spot_hourly = pd.read_csv('CSV/el_spot_hourly_2018.csv', sep=';', on_bad_lines='skip')
        if self.year == '2019':
            el_spot_hourly = pd.read_csv('CSV/el_spot_hourly_2019.csv', sep=';', on_bad_lines='skip')
        if self.year == '2020':
            el_spot_hourly = pd.read_csv('CSV/el_spot_hourly_2020.csv', sep=';', on_bad_lines='skip')
        if self.year == '2021':
            el_spot_hourly = pd.read_csv('CSV/el_spot_hourly_2021.csv', sep=';', on_bad_lines='skip')
        return el_spot_hourly

    def el_pris (self):
        nettleie = 27.9 / 100
        elavgift = 16.69 / 100
        fastledd = (115 * 12) / 8600
        pslag = 0
        moms = 1.25

        if self.region == 'Sørøst-Norge':
            el_pris_hourly = (self.el_spot_pris().iloc[:, 3] / 1000 + nettleie + elavgift + fastledd + pslag) * moms
        if self.region == 'Sørvest-Norge':
            el_pris_hourly = (self.el_spot_pris().iloc[:, 4] / 1000 + nettleie + elavgift + fastledd + pslag) * moms
        if self.region == 'Midt-Norge':
            el_pris_hourly = (self.el_spot_pris().iloc[:, 5] / 1000 + nettleie + elavgift + fastledd + pslag) * moms
        if self.region == 'Nord-Norge':
            el_pris_hourly = (self.el_spot_pris().iloc[:, 6] / 1000 + nettleie + elavgift + fastledd + pslag) * moms
        if self.region == 'Vest-Norge':
            el_pris_hourly = (self.el_spot_pris().iloc[:, 7] / 1000 + nettleie + elavgift + fastledd + pslag) * moms

        el_pris_hourly = np.array(el_pris_hourly)
        el_pris_hourly = np.resize(el_pris_hourly, 8760)

        return el_pris_hourly

    def beregn_el_pris (self):
        if self.year == 'Gjennomsnitt av de siste 4 år':
            gjennomsnitt_el_pris = 0
            for year in ['2018', '2019', '2020', '2021']:
                self.year = year
                el_pris_hourly = self.el_pris ()
                gjennomsnitt_el_pris += el_pris_hourly
            return gjennomsnitt_el_pris / 4
        else:
            return self.el_pris ()




class Dimensjonering:
    def __init__(self):
        pass

    @st.cache
    def energi_og_effekt_beregning(self, dekningsgrad, energibehov_arr, energibehov_sum):
        varmepumpe_storrelse = max(energibehov_arr)
        beregnet_dekningsgrad = 100.5
        if dekningsgrad == 100:
            return np.array(energibehov_arr), round(np.sum(energibehov_arr)), float("{:.1f}".format(varmepumpe_storrelse))

        while (beregnet_dekningsgrad / dekningsgrad) > 1:
            tmp_liste_h = np.zeros (8760)
            for i, timeverdi in enumerate (energibehov_arr):
                if timeverdi > varmepumpe_storrelse:
                    tmp_liste_h[i] = varmepumpe_storrelse
                else:
                    tmp_liste_h[i] = timeverdi
            
            beregnet_dekningsgrad = (sum (tmp_liste_h) / energibehov_sum) * 100

            varmepumpe_storrelse -= 0.05
        
        return np.array (tmp_liste_h), round (np.sum (tmp_liste_h)), float("{:.1f}".format(varmepumpe_storrelse))

    def angi_dekningsgrad(self):
        return st.number_input('Dekningsgrad til bergvarmeanlegget [%]', value=100, min_value=80, max_value=100, step = 1)

    def angi_cop(self):
        return st.number_input('Årsvarmefaktor (SCOP) til varmepumpen', value=3.5, min_value=2.0, max_value=4.0, step = 0.1)

    def dekning(self, energibehov_arr_gv, energibehov_arr, cop):
        levert_fra_bronner_arr = energibehov_arr_gv - energibehov_arr_gv / cop
        kompressor_arr = energibehov_arr_gv - levert_fra_bronner_arr
        spisslast_arr = energibehov_arr - energibehov_arr_gv

        levert_fra_bronner_sum = int(sum(levert_fra_bronner_arr))
        kompressor_sum = int(sum(kompressor_arr))
        spisslast_sum = int(sum(spisslast_arr))

        return levert_fra_bronner_arr, kompressor_arr, spisslast_arr, levert_fra_bronner_sum, kompressor_sum, spisslast_sum

    def energi_resultater(self, levert_fra_bronner_sum, kompressor_sum, spisslast_sum):
        column_1, column_2, column_3 = st.columns(3)
        with column_1:
            st.metric(label="Levert energi fra brønner", value=(str(round (levert_fra_bronner_sum, -1)) + " kWh"))
        with column_2:
            st.metric(label="Strømforbruk varmepumpe", value=(str(round (kompressor_sum, -1)) + " kWh"))
        with column_3:
            st.metric(label="Spisslast", value=(str(round (spisslast_sum, -1)) + " kWh"))

    def varighetsdiagram(self, energibehov_arr, energibehov_arr_gv, kompressor_arr):

        wide_form = pd.DataFrame({
            'Varighet (timer)' : np.array(range(0, len(energibehov_arr))),
            'Spisslast (ikke bergvarme)' : np.sort(energibehov_arr)[::-1], 
            'Levert energi fra brønn(er)' : np.sort(energibehov_arr_gv)[::-1],
            'Strømforbruk varmepumpe' : np.sort(kompressor_arr)[::-1]
            })

        c = alt.Chart(wide_form).transform_fold(
            ['Spisslast (ikke bergvarme)', 'Levert energi fra brønn(er)', 'Strømforbruk varmepumpe'],
            as_=['key', 'Effekt (kW)']).mark_area().encode(
                x=alt.X('Varighet (timer):Q'),
                y='Effekt (kW):Q',
                color=alt.Color('key:N', scale=alt.Scale(domain=['Spisslast (ikke bergvarme)', 'Levert energi fra brønn(er)', 'Strømforbruk varmepumpe'], 
                range=['#ffdb9a', '#48a23f', '#1d3c34']), legend=alt.Legend(orient='top', direction='vertical', title=None))
            )

        st.altair_chart(c, use_container_width=True)


        #Lock
        #lock = RendererAgg.lock
        #with lock:
        #    plt.fill_between(x_arr, np.sort(energibehov_arr)[::-1], label='Spisslast', color = '#F0F4E3')
        #    plt.fill_between(x_arr, np.sort(energibehov_arr_gv)[::-1], label='Levert energi fra brønn(er)', color ='#b7dc8f')
        #    plt.fill_between(x_arr, np.sort(kompressor_arr)[::-1], label='Strømforbruk varmepumpe', color = '#1d3c34')
            
        #    plt.xlabel('Varighet [timer]')
        #    plt.ylabel('Effekt [kW]')

        #    plt.rcParams['axes.facecolor'] = '#FFFFFF'
        #    plt.rcParams['savefig.facecolor'] = '#F6F8F1'

        #    plt.xlim(0,8760)
        #    plt.ylim(0, max(energibehov_arr))
        #    plt.grid()
        #    plt.legend()
        #    st.pyplot (plt)
        #    plt.close()

    def varighetsdiagram_bar(self, spisslast_arr, energibehov_arr_gv, kompressor_arr, levert_fra_bronner_arr):
        spisslast_arr = hour_to_month (spisslast_arr)
        energibehov_arr_gv = hour_to_month (energibehov_arr_gv)
        kompressor_arr = hour_to_month (kompressor_arr)
        levert_fra_bronner_arr = hour_to_month (levert_fra_bronner_arr)

        months = ['jan', 'feb', 'mar', 'apr', 'mai', 'jun', 'jul', 'aug', 'sep', 'okt', 'nov', 'des']
        x_axis = np.arange(len(months))

        data = pd.DataFrame({'Måneder' : months, 'Levert energi fra brønn(er)' : levert_fra_bronner_arr, 'Strømforbruk varmepumpe' : kompressor_arr, })
        c = alt.Chart(data).transform_fold(
            ['Levert energi fra brønn(er)', 'Strømforbruk varmepumpe'],
            as_=['Forklaring', 'Oppvarmingsbehov (kWh)']).mark_bar().encode(
            x=alt.X('Måneder:N', sort=months),
            y='Oppvarmingsbehov (kWh):Q',
            color=alt.Color('Forklaring:N', scale=alt.Scale(domain=['Levert energi fra brønn(er)', 'Strømforbruk varmepumpe'], 
            range=['#48a23f', '#1d3c34']), legend=alt.Legend(orient='top', direction='vertical', title=None)))
        st.altair_chart(c, use_container_width=True)

        #spisslast_label='Dekkes ikke\nav bergvarme:\n' + str(sum(spisslast_arr)) + ' kWh'
        #levert_energi_label='Levert energi \nfra brønn(er):\n' + str(sum(levert_fra_bronner_arr)) + ' kWh'
        #kompressor_label='Strømforbruk \nvarmepumpe:\n' + str(sum(kompressor_arr)) + ' kWh'
        
        #Lock
        #lock = RendererAgg.lock
        #with lock:
        #    plt.bar(x_axis, levert_fra_bronner_arr, 0.4, label=levert_energi_label, color ='#b7dc8f', bottom = kompressor_arr)
        #    plt.bar(x_axis, kompressor_arr, 0.4, label=kompressor_label, color = '#1d3c34')
        #    plt.bar(x_axis, spisslast_arr, 0.4, label=spisslast_label, color = '#F0F4E3', bottom = energibehov_arr_gv)
        #    plt.rcParams['axes.facecolor'] = '#FFFFFF'
        #    plt.rcParams['savefig.facecolor'] = '#F6F8F1'
        #    plt.xticks(x_axis, months)
        #    plt.legend(bbox_to_anchor=(0,1.02,1,0.2), loc="lower left", mode="expand", borderaxespad=0, ncol=3)
        #    plt.grid()
        #    plt.ylabel("Oppvarmingsbehov [kWh]")
        #    st.pyplot(plt)
        #    plt.close()

    def antall_meter(self, varmepumpe_storrelse, levert_fra_bronner, cop):
        energi_per_meter = 80  # kriterie 1
        effekt_per_meter = 30  # kriterie 2
        
        antall_meter_effekt = ((varmepumpe_storrelse - varmepumpe_storrelse / cop) * 1000) / effekt_per_meter
        antall_meter_energi = (levert_fra_bronner) / energi_per_meter

        if antall_meter_effekt < antall_meter_energi:
            antall_meter_tot = antall_meter_energi
        else:
            antall_meter_tot = antall_meter_effekt

        return int(antall_meter_tot)

    def antall_bronner(self, antall_meter):
        bronnlengde = 0
        for i in range(1,10):
            bronnlengde += 350
            if antall_meter <= bronnlengde:
                return i

    def bronn_resultater(self, antall_meter, varmepumpe_storrelse, antall_bronner):
        column_1, column_2, column_3 = st.columns(3)
        with column_1:
            st.metric(label="Totalt antall brønnmeter", value=str(antall_meter) + " m")
        with column_2:
            st.metric(label="Varmepumpestørrelse", value=str(math.ceil(varmepumpe_storrelse)) + " kW")
        with column_3:
            st.metric(label='Antall brønner', value = str(antall_bronner))




class Energibehov:
    def __init__(self):
        pass

    @st.cache
    def totalt_behov_fra_fil(self, stasjon_id, areal):
        dhw = 'Database/' + stasjon_id + '_dhw.csv'
        romoppvarming = 'Database/' + stasjon_id + '_romoppvarming.csv'
        dhw_arr = pd.read_csv(dhw, sep=',', on_bad_lines='skip').to_numpy() * areal
        romoppvarming_arr = pd.read_csv(romoppvarming, sep=',', on_bad_lines='skip').to_numpy() * areal
        return dhw_arr, romoppvarming_arr

    def resultater(self, dhw_sum, romoppvarming_sum, energibehov_sum):
        st.metric(label="Årlig oppvarmingsbehov", value=(str(round ((dhw_sum + romoppvarming_sum), -1)) + " kWh"))

    def plot(self, dhw_arr, romoppvarming_arr):
        dhw_arr = hour_to_month (dhw_arr)
        romoppvarming_arr = hour_to_month (romoppvarming_arr)
        months = ['jan', 'feb', 'mar', 'apr', 'mai', 'jun', 'jul', 'aug', 'sep', 'okt', 'nov', 'des']
        x_axis = np.arange(len(months))

        data = pd.DataFrame({'Måneder' : months, 'Romoppvarmingsbehov' : romoppvarming_arr, 'Varmtvannsbehov' : dhw_arr, })
        c = alt.Chart(data).transform_fold(
            ['Romoppvarmingsbehov', 'Varmtvannsbehov'],
            as_=['Forklaring', 'Oppvarmingsbehov (kWh)']).mark_bar().encode(
            x=alt.X('Måneder:N', sort=months, title=None),
            y='Oppvarmingsbehov (kWh):Q',
            color=alt.Color('Forklaring:N', scale=alt.Scale(domain=['Romoppvarmingsbehov', 'Varmtvannsbehov'], 
            range=['#4a625c', '#8e9d99']), legend=alt.Legend(orient='top', direction='vertical', title=None)))
        st.altair_chart(c, use_container_width=True)

        



        #plt.bar(x_axis, dhw_arr, 0.4, label = 'Varmtvannsbehov', color = '#1d3c34')
        #plt.bar(x_axis, romoppvarming_arr, 0.4, label = 'Romoppvarmingsbehov', color = '#48a23f', bottom = dhw_arr)
        #plt.rcParams['axes.facecolor'] = '#FFFFFF'
        #plt.rcParams['savefig.facecolor'] = '#F6F8F1'
        #plt.xticks(x_axis, months)
        #plt.legend(bbox_to_anchor=(0,1.02,1,0.2), loc="lower left", mode="expand", borderaxespad=0, ncol=3)
        #plt.grid()
        #plt.ylabel("Oppvarmingsbehov [kWh]")
        #st.pyplot(plt)
        #plt.close()

    def aarlig_behov(self, dhw_arr, romoppvarming_arr):
        dhw_sum = int(sum(dhw_arr))
        romoppvarming_sum = int(sum(romoppvarming_arr))
        energibehov_sum = dhw_sum + romoppvarming_sum
        return int(dhw_sum), int(romoppvarming_sum), int(energibehov_sum)
        
    def juster_behov(self, dhw_sum, romoppvarming_sum, dhw_arr, romoppvarming_arr):
        dhw_sum_ny = st.number_input('Varmtvannsbehov [kWh]', min_value = int(dhw_sum*0.1), max_value = int(dhw_sum*5), value = round(dhw_sum, -1), step = int(500))
        romoppvarming_sum_ny = st.number_input('Romoppvarmingsbehov [kWh]', min_value = int(romoppvarming_sum*0.1), max_value = int(romoppvarming_sum*5), value = round (romoppvarming_sum, -1), step = int(500))
        dhw_prosent = dhw_sum_ny / dhw_sum
        romoppvarming_prosent = romoppvarming_sum_ny / romoppvarming_sum

        dhw_arr = dhw_arr * dhw_prosent
        romoppvarming_arr = romoppvarming_arr * romoppvarming_prosent

        return dhw_sum_ny, romoppvarming_sum_ny, dhw_arr, romoppvarming_arr




class Temperaturdata ():
    def __init__(self, lat, long):
        self.lat = lat
        self.long = long

    @st.cache
    def temperaturserie_fra_fil(self):
        serie = 'Database/' + self.stasjon_id + '_temperatur.csv'
        temperatur_arr = pd.read_csv(serie, sep=',', on_bad_lines='skip').to_numpy()
        return temperatur_arr

    def gjennomsnittstemperatur(self):
        arr = self.temperaturserie_fra_fil()
        return float(np.average(arr))

    @st.cache
    def importer_csv (self):
        stasjonsliste = pd.read_csv('Database/Stasjoner.csv', sep=',',on_bad_lines='skip')
        return stasjonsliste

    def nearmeste_stasjon (self):
        distanse_min = 1000000
        df = self.importer_csv()
        for i in range (0, len (df)):
            distanse = mpu.haversine_distance((df.iat [i,1], df.iat [i,2]), (self.lat, self.long))
            if distanse != 0 and distanse < distanse_min:
                distanse_min = distanse
                stasjon_id = df.iat [i,0]
                stasjon_lat = df.iat [i,1]
                stasjon_long = df.iat [i,2]

                self.stasjon_id = stasjon_id

        return stasjon_id, stasjon_lat, stasjon_long, distanse_min




class Energibronn:
    def __init__(self, lat, long):
        df = self.importer_csv ()
        self.les_csv(df)
        self.lat = lat
        self.long = long

    @st.cache
    def importer_csv (self):
        energibronner_df = pd.read_csv('CSV/energibronner.csv', sep=';', on_bad_lines='skip', low_memory=False)
        return energibronner_df

    def les_csv (self, energibronner_df):
        self.energibronner_boret_lengde_til_berg = energibronner_df.iloc[:, 10]
        self.energibronner_lat = energibronner_df.iloc[:, -2]
        self.energibronner_long = energibronner_df.iloc[:, -3]

    def dybde_til_fjell (self):
        minste_distanse = 100000
        for i in range(0, len(self.energibronner_long)):
            distanse = mpu.haversine_distance((self.energibronner_lat.iloc[i], self.energibronner_long.iloc[i]),
                                              (self.lat, self.long))
            if minste_distanse > distanse:
                minste_distanse = distanse
                minste_i = i

        distanse_til_energibronn = round(distanse)
        dybde_til_fjell = round(self.energibronner_boret_lengde_til_berg.iloc[minste_i])
        energibronn_long = self.energibronner_long.iloc[minste_i]
        energibronn_lat = self.energibronner_lat.iloc[minste_i]
        return dybde_til_fjell, energibronn_lat, energibronn_long



class Gis:
    def __init__(self):
        pass

    def adresse_til_koordinat (self, adresse):
        geolocator = Nominatim(user_agent="my_request")
        location = geolocator.geocode(adresse, timeout=None)
        if location is None:
            st.error ('Ugyldig adresse. Prøv igjen!')
            #lott = load_lottie('https://assets2.lottiefiles.com/packages/lf20_i0hpsr18.json')
            #st_lottie(lott)
            st.stop()
        lat = location.latitude
        long = location.longitude
        return lat, long

    def kart(self, stasjon_lat, adresse_lat, energibronn_lat, stasjon_long, adresse_long, energibronn_long):
        df1 = pd.DataFrame({'latitude': [stasjon_lat],'longitude': [stasjon_long]})
        df2 = pd.DataFrame({'latitude': [adresse_lat],'longitude': [adresse_long]})
        df3 = pd.DataFrame({'latitude': [energibronn_lat],'longitude': [energibronn_long]})
        
        st.pydeck_chart(pdk.Deck(
            map_style='mapbox://styles/mapbox/streets-v11',
            initial_view_state=pdk.ViewState(
                latitude=adresse_lat,
                longitude=adresse_long,
                zoom=15,
                pitch=50,
            ),
            layers=[
                pdk.Layer(
                    'ScatterplotLayer',
                    data=df1,
                    get_position='[longitude, latitude]',
                    get_radius=50,
                    pickable=True,
                    stroked=True,
                    filled=True,
                    get_fill_color=[0, 0, 255],
                    get_line_color=[0, 0, 0],
                ),
                pdk.Layer(
                    'ScatterplotLayer',
                    data=df2,
                    get_position='[longitude, latitude]',
                    get_radius=15,
                    pickable=True,
                    stroked=True,
                    filled=True,
                    get_fill_color=[255, 0, 0],
                    get_line_color=[0, 0, 0],
                ),
                pdk.Layer(
                    'ScatterplotLayer',
                    data=df3,
                    get_position='[longitude, latitude]',
                    get_radius=5,
                    pickable=True,
                    stroked=True,
                    filled=True,
                    get_fill_color=[0, 255, 0],
                    get_line_color=[0, 0, 0],
                ),
            ],
        ))




class Forside:
    def __init__(self):
        pass

    def overskrift(self):
        return 'Inndata'

    def tittel(self):
        return 'Bergvarmekalkulatoren'

    def favicon(self):
        return Image.open('Bilder/AsplanViak_Favicon_16x16.png')

    def forsidebilde(self):
        image = Image.open('Bilder/hovedlogo.png')
        st.image(image)

    def innstillinger(self):
        st.set_page_config(
        page_title=self.tittel(),
        page_icon=self.favicon(),
        layout="centered",
        )

        hide_menu_style = """
                        <style>
                        #MainMenu {visibility: hidden; }
                        footer {visibility: hidden; }
                        </style>
        """
        st.markdown(hide_menu_style,unsafe_allow_html=True)

    def input(self):
         bolig_areal = st.number_input('Oppgi oppvarmet bruksareal [m2]', min_value=1, value=150, max_value=1000, step=10)
         adresse = st.text_input('Hva er din adresse?', placeholder = 'Karl Johans Gate 22, Oslo')
         return adresse, bolig_areal

    def start_button(self):
        press_start = st.button('Start beregning','press_start')
        return press_start
