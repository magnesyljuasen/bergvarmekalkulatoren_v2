import streamlit as st
from utilities import Dimensjonering, Forside, Gis, Energibronn, Strompriser, Temperaturdata, Energibehov, Kostnader, Co2, Veienvidere, load_lottie
from streamlit_lottie import st_lottie
from datetime import datetime


#with st.expander ('Velg betingelser for dimensjoneringen'):
#    st.write(""" For å dimensjonere ditt bergvarmeanlegg må du angi dekningsgraden til anlegget. Vanligvis settes
#    #dekningsgraden til 100% som betyr at bergvarmeanlegget skal dimensjoneres for å dekke hele 
#    #energibehovet. Spisslasten må dekkes av noe annet enn bergvarmeanlegget som f.eks. vedfyring eller strøm. """)
#    st.write (""" Teoretisk årsvarmefaktor (Seasonal Coefficient of Performance) finner du på varmepumpens energimerke. 
#    SCOP er beregnet ut fra fabrikkdata. Den angir hvor mye mer varme en varmepumpe i beste fall kan levere, 
#    sammenlignet med hva den bruker i strøm. I praksis er det vanskelig å oppnå så høye tall – 
#    og dermed strømsparing – i virkeligheten.""")

#st.header ('Grønne lån')
#    st.write (""" Grønne energilån er lån til bærekraftige formål som for eksempel etablering av et bergvarmeanlegg.
#    Du kan dermed låne penger til å dekke investeringskostnaden. I grafen under kan du justere låneparameterene 
#    nedbetalingstid og effektiv rente, for så å få ut den årlige kostnadsutviklingen. """)
#    with st.expander ('Velg betingselser for beregningen'):
#        kostnader_obj.gronne_laan()

#Inndata
#Gjør alle beregninger
#Så mulighet for å justere 

forside_obj = Forside()
forside_obj.innstillinger()

def main ():
    #-----------Sidebar
    #Inndata
    with st.sidebar:   
        forside_obj.forsidebilde()
        st.title (forside_obj.overskrift())
        adresse, bolig_areal = forside_obj.input()
    if not adresse:
        st.title('Bergvarmekalkulatoren')
        lott = load_lottie('https://assets5.lottiefiles.com/packages/lf20_l22gyrgm.json')
        st_lottie(lott)
        st.header('👈Kalkuler din gevinst ved å hente energi fra berggrunnen!')

        st.markdown("""---""")

        st.header('Hvorfor bergvarme?')
        st.write(""" Bergvarme er både miljøvennlig, kortreist og fornybar energi, 
                     og blir stadig mer populært blant norske byggeiere. Et bergvarmeanlegg gir den 
                     beste energibesparelsen og kan redusere din strømregning med en faktor på 3 – 4.  
        """)

        st.header('Hva er bergvarme?')
        st.write(""" Bergvarme er i hovedsak lagret solenergi som har en 
                     stabil temperatur i størrelsesorden rundt 5 til 7 °C. For å hente ut bergvarme fra grunnen
                     må det bores en energibrønn. Inne i energibrønnen monteres det en U-formet plastslange som fylles med en sirkulerende
                     frostsikker væske. Væsken varmes opp av berggrunnen, og varmeenergien kan nå utnyttes ved hjelp av en 
                     væske-vann-varmepumpe for å levere høy temperatur til boligens vannbårne varmesystem. 
                     """) 

        st.write(""" Om sommeren, når det er behov for kjøling, er temperaturen i brønnen i seg selv
                     lav nok til å kjøle bygningen. Da trengs viftekonvektorer som kan 
                     fordele kjøling i bygningen på en komfortabel måte. 
        """)

        st.header('Om kalkulatoren')
        st.write(""" Disclaimer ...
        """)
        st.stop()

    with st.spinner('Kalkulerer'):
        #-----------
        #Beregning - GIS
        adresse_lat, adresse_long = Gis().adresse_til_koordinat(adresse)
        dybde_til_fjell, energibronn_lat, energibronn_long = Energibronn(adresse_lat, adresse_long).dybde_til_fjell()
        temperaturdata_obj = Temperaturdata(adresse_lat,adresse_long)
        stasjon_id, stasjon_lat, stasjon_long, distanse_min = temperaturdata_obj.nearmeste_stasjon()
        #st.write (temperaturdata_obj.gjennomsnittstemperatur())
        
        st.title('Resultater')
        #Fremvisning - GIS
        st.header('Oversiktskart')
        Gis().kart(stasjon_lat, adresse_lat, energibronn_lat, stasjon_long, adresse_long, energibronn_long)
        with st.expander ('Hva viser kartet?'):
            st.write (""" Kartet viser adresse, nærmeste eksisterende energibrønn og nærmeste værstasjon med fullstendige. 
            Nærmeste eksisterende energibrønn brukes til å estimere dybde til fjell i området. 
            Fra værstasjonen hentes det inn målt temperatur per time for de siste 4 år. """)

        #-----------Sidebar
        with st.sidebar:
            st.title('Variabler')
            st.markdown('Parameterene under kan justeres ved behov')


        #Beregning - Energibehov
        energibehov_obj = Energibehov()
        dhw_arr, romoppvarming_arr = energibehov_obj.totalt_behov_fra_fil(stasjon_id, bolig_areal)
        dhw_sum, romoppvarming_sum, energibehov_sum = energibehov_obj.aarlig_behov(dhw_arr, romoppvarming_arr)
        #-----------Sidebar
        with st.sidebar:
            dhw_sum, romoppvarming_sum, dhw_arr, romoppvarming_arr = energibehov_obj.juster_behov(dhw_sum, romoppvarming_sum, dhw_arr, romoppvarming_arr)
        #-----------
        #energibehov_obj.resultater(dhw_sum, romoppvarming_sum, energibehov_sum)

        #Fremvisning - Energibehov
        st.header('Oppvarmingsbehov for din bolig')
        energibehov_obj.plot(dhw_arr, romoppvarming_arr)
        with st.expander ('Hvordan beregnes oppvarmingsbehovet?'):
            st.write (""" Gjennomsnittstemperatur fra de siste 4 år og oppgitt boligareal benyttes til å estimere 
            oppvarmingsbehovet for din bolig. Beregningen gjøres ved hjelp av PROFet som er utviklet av Sintef. 
            Verktøyet estimerer både det årlige behovet for romoppvarming- og varmtvann som til sammen
            utgjør det totale årlige oppvarmingsbehovet for din bolig. """)

        energibehov_arr = (dhw_arr + romoppvarming_arr).reshape(-1)


        #Beregning - Dimensjonering
        dimensjonering_obj = Dimensjonering()
        #-----------Sidebar
        with st.sidebar:       
            dekningsgrad = dimensjonering_obj.angi_dekningsgrad()
            cop = dimensjonering_obj.angi_cop()
        #-----------
        energibehov_arr_gv, energibehov_sum_gv, varmepumpe_storrelse = dimensjonering_obj.energi_og_effekt_beregning(dekningsgrad, energibehov_arr, energibehov_sum)
        levert_fra_bronner_arr, kompressor_arr, spisslast_arr, levert_fra_bronner_sum, kompressor_sum, spisslast_sum = dimensjonering_obj.dekning(energibehov_arr_gv, energibehov_arr, cop)
        antall_meter = dimensjonering_obj.antall_meter(varmepumpe_storrelse, levert_fra_bronner_sum, cop)
        antall_bronner = dimensjonering_obj.antall_bronner (antall_meter)

        #Fremvisning - Dimensjonering 
        st.header('Dimensjonering av ditt bergvarmeanlegg') 
        dimensjonering_obj.varighetsdiagram_bar(spisslast_arr, energibehov_arr_gv, kompressor_arr, levert_fra_bronner_arr)
        dimensjonering_obj.bronn_resultater(antall_meter, varmepumpe_storrelse, antall_bronner)
        
        with st.expander('Hvordan dimensjoneres et bergvarmeanlegg?'):
            st.write(""" ...
            
            """)
        

        #Beregning og fremvisning - CO2
        st.header ('Et miljøvennlig alternativ')
        Co2().beregning(energibehov_arr, kompressor_sum)
        with st.expander ('Hvordan beregnes dette?'):
            st.write(""" ...
            
            """)


        #Beregning - Kostnader
        strompriser_obj = Strompriser()
        #-----------Sidebar
        with st.sidebar:   
            strompriser_obj.input()
        #-----------
        el_pris = strompriser_obj.beregn_el_pris()
        kostnader_obj = Kostnader(dybde_til_fjell, varmepumpe_storrelse, antall_meter, kompressor_arr, energibehov_arr_gv, el_pris)
        #-----------Sidebar
        with st.sidebar:   
            kostnader_obj.oppdater_dybde_til_fjell()
        #-----------


        #Fremvisning - Kostnader
        st.header ('Bergvarme reduserer dine månedlige utgifter')
        kostnader_obj.monthly_costs()

        st.header ('Investeringskostnad')
        st.write (""" Den største barrieren når det gjelder etablering av bergvarmeanlegg er investeringskostnaden.
        Investeringskostnaden inkluderer boring av energibrønn samt installasjon av varmepumpe. """)
        kostnader_obj.plot_investeringskostnad()


        #Avslutning
        st.markdown("""---""")
        Veienvidere()
        st.caption('Et verktøy fra Asplan Viak AS | 📧 magne.syljuasen@asplanviak.no')

main ()
