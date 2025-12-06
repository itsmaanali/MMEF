package org.mmef.demo;


import org.cloudsimplus.allocationpolicies.VmAllocationPolicySimple;
import org.cloudsimplus.brokers.DatacenterBrokerSimple;
import org.cloudsimplus.cloudlets.Cloudlet;
import org.cloudsimplus.cloudlets.CloudletSimple;
import org.cloudsimplus.core.CloudSimPlus;
import org.cloudsimplus.datacenters.Datacenter;
import org.cloudsimplus.datacenters.DatacenterSimple;
import org.cloudsimplus.hosts.Host;
import org.cloudsimplus.hosts.HostSimple;
import org.cloudsimplus.power.models.PowerModelHostSimple;
import org.cloudsimplus.resources.Pe;
import org.cloudsimplus.resources.PeSimple;
import org.cloudsimplus.schedulers.cloudlet.CloudletSchedulerTimeShared;
import org.cloudsimplus.utilizationmodels.UtilizationModelDynamic;
import org.cloudsimplus.vms.Vm;
import org.cloudsimplus.vms.VmSimple;

import java.io.BufferedWriter;
import java.io.FileWriter;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Random;

public class TelemetryDemo {
    private static final int HOSTS = 3;
    private static final int HOST_PES = 8;     // CPU cores per host
    private static final int VMS = 6;
    private static final int VM_PES = 2;       // CPU cores per VM
    private static final int CLOUDLETS = 30;

    private static final double SIM_END = 300; // seconds
    private static final double FAULT_START = 120; // when "fault" begins

    private boolean faultActive = false;
    private BufferedWriter writer;

    public static void main(String[] args) throws Exception {
        new TelemetryDemo().run();
    }

    private void run() throws Exception {
        // Ensure output dir exists
        Path outDir = Path.of("telemetry");
        Files.createDirectories(outDir);
        writer = new BufferedWriter(new FileWriter(outDir.resolve("metrics.csv").toFile()));
        writer.write("time_s,host_id,vm_id,cpu_util,power_w,temp_c,label\n");

        CloudSimPlus sim = new CloudSimPlus();

        Datacenter dc = createDatacenter(sim);
        DatacenterBrokerSimple broker = new DatacenterBrokerSimple(sim);

        List<Vm> vms = createVms();
        List<Cloudlet> cloudlets = createCloudlets();

        broker.submitVmList(vms);
        broker.submitCloudletList(cloudlets);

        // Telemetry tick: every 1.0 simulated second
        sim.addOnClockTickListener(info -> {
            double t = info.getTime();
            if (!faultActive && t >= FAULT_START) {
                faultActive = true; // start the fault event
            }
            try {
                logTelemetry(t, dc, vms);
            } catch (IOException e) {
                e.printStackTrace();
            }
        });

        sim.terminateAt(SIM_END);
        sim.start();

        writer.flush();
        writer.close();

        System.out.println("Done. CSV written to telemetry/metrics.csv");
    }

    private Datacenter createDatacenter(CloudSimPlus sim) {
        List<Host> hostList = new ArrayList<>();
        for (int i = 0; i < HOSTS; i++) {
            List<Pe> pes = new ArrayList<>();
            for (int p = 0; p < HOST_PES; p++) {
                pes.add(new PeSimple(1000)); // 1000 MIPS per core
            }
            long ram = 64_000;  // MB
            long bw = 100_000;  // Mbps
            long storage = 1_000_000; // MB

            HostSimple host = new HostSimple(ram, bw, storage, pes);
            // Simple power model: base 200W + linear increase with CPU
            host.setPowerModel(new PowerModelHostSimple(300, 200)); // (staticW, maxDynamicW)

            hostList.add(host);
        }
        return new DatacenterSimple(sim, hostList, new VmAllocationPolicySimple());
    }

    private List<Vm> createVms() {
        List<Vm> vms = new ArrayList<>();
        for (int i = 0; i < VMS; i++) {
            Vm vm = new VmSimple(1000, VM_PES); // mips, PEs
            vm.setId(i);
            vm.setRam(4096).setBw(10_000).setSize(10_000);
            vm.setCloudletScheduler(new CloudletSchedulerTimeShared());
            vms.add(vm);
        }
        return vms;
    }

    private List<Cloudlet> createCloudlets() {
        List<Cloudlet> list = new ArrayList<>();
        long len = 20_000; // MI
        long fileSize = 300;
        long outputSize = 300;
        UtilizationModelDynamic cpuUtil = new UtilizationModelDynamic(0.5); // avg 50%
        for (int i = 0; i < CLOUDLETS; i++) {
            Cloudlet cl = new CloudletSimple(len, VM_PES);
            cl.setFileSize(fileSize).setOutputSize(outputSize);
            cl.setUtilizationModelCpu(cpuUtil);
            list.add(cl);
        }
        return list;
    }

    private void logTelemetry(double t, Datacenter dc, List<Vm> vms) throws IOException {
        Random rnd = new Random(42);

        // Approximate total datacenter power by summing host power draw
        double datacenterPower = dc.getHostList().stream()
                .mapToDouble(host -> host.getPowerModel().getPower(host.getCpuPercentUtilization()))
                .sum();

        for (Vm vm : vms) {
            double baseCpu = vm.getCpuPercentUtilization();
            if (Double.isNaN(baseCpu)) {
                baseCpu = 0.3 + 0.2 * Math.sin(t / 30.0);
            }

            double cpu = baseCpu + (faultActive ? 0.25 : 0.0);
            cpu = Math.max(0, Math.min(0.99, cpu));

            double power = datacenterPower + rnd.nextDouble() * 5.0;

            double hostTempBaseline = 35 + cpu * 30;
            double temp = hostTempBaseline + (faultActive ? 5 : 0) + rnd.nextGaussian();

            int label = faultActive ? 1 : 0;
            long hostId = vm.getHost() == null ? -1 : vm.getHost().getId();

            writer.write(String.format(Locale.US,
                    "%.1f,%d,%d,%.3f,%.2f,%.1f,%d%n",
                    t,
                    hostId,
                    vm.getId(),
                    cpu,
                    power,
                    temp,
                    label));
        }
    }
}
